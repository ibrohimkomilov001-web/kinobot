#!/usr/bin/env bash
# Kino Makoni API — EC2'da bir buyruq bilan o'rnatish / yangilash.
#
# Birinchi marta (Telegram ma'lumotlari bilan):
#   curl -fsSL https://raw.githubusercontent.com/ibrohimkomilov001-web/kinobot/refs/heads/claude/eager-lovelace-0db0j8/kino-makoni/deploy/bootstrap.sh -o bootstrap.sh
#   TG_API_ID=... TG_API_HASH=... TG_HELPER_BOT_TOKEN=... DOMAIN=kinomakoni.uz bash bootstrap.sh
#
# Keyingi yangilanishlar:  bash ~/KINO_MAKONI_APP/kino-makoni/deploy/bootstrap.sh
#
# Nima qiladi:
#   1. 1 GB swap (bo'lmasa), repodan FAQAT kino-makoni/ papkasini oladi
#   2. Botning .env faylini FAQAT O'QIYDI: DATABASE_URL va BASE_CHANNEL_ID
#   3. Bot bazasida o'qish-uchun rol (kino_makoni_reader, faqat SELECT) va
#      ilova uchun ALOHIDA baza (kino_makoni_app) yaratadi — bot jadvallariga
#      hech narsa yozilmaydi
#   4. .env yozadi, Docker'da API + Caddy'ni ko'taradi, Telegram'ni tekshiradi
#
# Botning konteyneri va ~/KINO_MAKON papkasi o'zgartirilmaydi.
set -euo pipefail

BRANCH="${BRANCH:-claude/eager-lovelace-0db0j8}"
REPO_URL="${REPO_URL:-https://github.com/ibrohimkomilov001-web/kinobot.git}"
APP_DIR="${APP_DIR:-$HOME/KINO_MAKONI_APP}"
BOT_ENV="${BOT_ENV:-$HOME/KINO_MAKON/.env}"
PG_IMAGE="postgres:16-alpine"
READER_ROLE="kino_makoni_reader"
APP_ROLE="kino_makoni_app"
APP_DB="kino_makoni_app"
PROJECT="kino-makoni-app"

say()  { printf '\n\033[1;33m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m  ✓ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;31m  ! %s\033[0m\n' "$*"; }
die()  { printf '\n\033[1;31mXATO: %s\033[0m\n' "$*" >&2; exit 1; }

# ---------- .env yordamchilari (qiymatdagi maxsus belgilar xavfsiz) ----------
env_get() { # env_get KEY FILE -> qiymat (tashqi qo'shtirnoqsiz)
  [ -f "$2" ] || return 0
  awk -v k="$1" '
    $0 ~ "^[[:space:]]*(export[[:space:]]+)?" k "[[:space:]]*=" {
      sub(/^[^=]*=[[:space:]]*/, ""); sub(/[[:space:]]+$/, "")
      if ($0 ~ /^".*"$/ || $0 ~ /^'\''.*'\''$/) $0 = substr($0, 2, length($0) - 2)
      v = $0
    }
    END { if (v != "") print v }' "$2"
}
env_set() { # env_set KEY VALUE FILE
  KEY="$1" VAL="$2" awk '
    BEGIN { k = ENVIRON["KEY"]; v = ENVIRON["VAL"]; done = 0 }
    $0 ~ "^" k "=" { print k "=" v; done = 1; next }
    { print }
    END { if (!done) print k "=" v }' "$3" > "$3.tmp" && mv "$3.tmp" "$3"
}
rand() { # pipefail bilan xavfsiz (tr|head SIGPIPE bermaydi)
  python3 -c 'import secrets,string,sys;a=string.ascii_letters+string.digits;print("".join(secrets.choice(a) for _ in range(int(sys.argv[1]))))' "${1:-32}"
}

# Prisma URL'idagi faqat Prisma'ga tegishli parametrlarni olib tashlaydi
clean_pg_url() {
  python3 - "$1" <<'PY'
import sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
u = urlsplit(sys.argv[1])
drop = {"schema", "pgbouncer", "connection_limit", "pool_timeout", "connect_timeout",
        "socket_timeout", "statement_cache_size", "channel_binding"}
q = [(k, v) for k, v in parse_qsl(u.query) if k not in drop]
scheme = "postgresql" if u.scheme in ("postgres", "postgresql") else u.scheme
print(urlunsplit((scheme, u.netloc, u.path, urlencode(q), "")))
PY
}
# URL'dagi foydalanuvchi/parol/bazani almashtiradi; asyncpg=1 bo'lsa SQLAlchemy formatiga
rewrite_pg_url() { # rewrite_pg_url URL USER PASS DB ASYNCPG
  python3 - "$@" <<'PY'
import sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode, quote
url, user, pw, db, asy = sys.argv[1:6]
u = urlsplit(url)
host = u.hostname or ""
if ":" in host:
    host = f"[{host}]"
netloc = f"{quote(user, safe='')}:{quote(pw, safe='')}@{host}" + (f":{u.port}" if u.port else "")
q = dict(parse_qsl(u.query))
if asy == "1":
    ssl = q.pop("sslmode", None)
    q = {k: v for k, v in q.items() if k in ("options",)}
    if ssl and ssl != "disable":
        q["ssl"] = "require"
    scheme = "postgresql+asyncpg"
else:
    scheme = "postgresql"
print(urlunsplit((scheme, netloc, "/" + db, urlencode(q), "")))
PY
}
url_host() { python3 -c 'import sys;from urllib.parse import urlsplit;print(urlsplit(sys.argv[1]).hostname or "")' "$1"; }
psql_run() { # psql_run URL [psql argumentlari...]  (stdin — SQL)
  local url="$1"; shift
  docker run --rm -i --network "${PSQL_NET:-host}" "$PG_IMAGE" psql "$url" -v ON_ERROR_STOP=1 -X -q "$@"
}

# ---------- 0. Tekshiruvlar ----------
say "Tizim tekshirilmoqda"
command -v docker >/dev/null || die "docker topilmadi"
docker compose version >/dev/null 2>&1 || die "docker compose (v2) topilmadi"
command -v git >/dev/null || die "git topilmadi"
command -v python3 >/dev/null || die "python3 topilmadi"
docker info >/dev/null 2>&1 || die "Docker'ga ulanib bo'lmadi (foydalanuvchi docker guruhida emasmi? 'sudo usermod -aG docker \$USER' va qayta kiring)"
ok "docker, compose, git, python3"

# ---------- 1. Swap (t3.micro: 1 GB RAM) ----------
if [ -z "$(swapon --noheadings 2>/dev/null)" ]; then
  say "1 GB swap yaratilmoqda"
  if sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile >/dev/null \
     && sudo swapon /swapfile; then
    grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
    ok "swap yoqildi"
  else
    warn "swap yaratib bo'lmadi — davom etamiz"
  fi
fi

# ---------- 2. Kod (faqat kino-makoni/ papkasi) ----------
say "Kod yuklanmoqda ($BRANCH)"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone -q --filter=blob:none --sparse -b "$BRANCH" "$REPO_URL" "$APP_DIR"
  git -C "$APP_DIR" sparse-checkout set kino-makoni
else
  git -C "$APP_DIR" fetch -q origin "$BRANCH"
  git -C "$APP_DIR" checkout -q "$BRANCH"
  git -C "$APP_DIR" reset -q --hard "origin/$BRANCH"
fi
ok "$(git -C "$APP_DIR" log -1 --format='%h %s')"

DEPLOY_DIR="$APP_DIR/kino-makoni/deploy"
ENV_FILE="$DEPLOY_DIR/.env"
COMPOSE=(docker compose -p "$PROJECT" -f "$DEPLOY_DIR/docker-compose.yml")

# ---------- 3. .env ----------
say ".env tayyorlanmoqda"
if [ ! -f "$ENV_FILE" ]; then
  grep -v '^[[:space:]]*#' "$APP_DIR/kino-makoni/backend/.env.example" | grep -v '^[[:space:]]*$' > "$ENV_FILE"
  ok "yangi .env yaratildi"
fi
chmod 600 "$ENV_FILE"

for key in TG_API_ID TG_API_HASH TG_HELPER_BOT_TOKEN; do
  if [ -n "${!key:-}" ]; then env_set "$key" "${!key}" "$ENV_FILE"; fi
done
[ "$(env_get TG_API_ID "$ENV_FILE")" != "0" ] && [ -n "$(env_get TG_API_ID "$ENV_FILE")" ] \
  || die "TG_API_ID berilmagan. Birinchi marta: TG_API_ID=... TG_API_HASH=... TG_HELPER_BOT_TOKEN=... bash bootstrap.sh"
[ -n "$(env_get TG_API_HASH "$ENV_FILE")" ] || die "TG_API_HASH berilmagan"
[ -n "$(env_get TG_HELPER_BOT_TOKEN "$ENV_FILE")" ] || die "TG_HELPER_BOT_TOKEN berilmagan"

DOMAIN="${DOMAIN:-$(env_get API_DOMAIN "$ENV_FILE" | sed -n 's/^api\.//p')}"
DOMAIN="${DOMAIN:-kinomakoni.uz}"
env_set API_DOMAIN "api.$DOMAIN" "$ENV_FILE"
env_set STREAM_DOMAIN "stream.$DOMAIN" "$ENV_FILE"
env_set API_PUBLIC_BASE_URL "https://api.$DOMAIN" "$ENV_FILE"
env_set STREAM_PUBLIC_BASE_URL "https://stream.$DOMAIN" "$ENV_FILE"
env_set TG_SESSION_DIR "/data" "$ENV_FILE"
env_set CORS_ORIGINS "[]" "$ENV_FILE"

SK="$(env_get SECRET_KEY "$ENV_FILE")"
if [ "${#SK}" -lt 32 ] || [[ "$SK" == change-me* ]]; then
  env_set SECRET_KEY "$(rand 48)" "$ENV_FILE"
  ok "SECRET_KEY yaratildi"
fi

# ---------- 4. Bot sozlamalari (faqat o'qish) ----------
# Bot .env fayli bo'lsa undan, bo'lmasa ishlab turgan bot konteyneridan
# (BASE_CHANNEL_ID muhit o'zgaruvchisi bor konteyner) o'qiladi.
ct_env() { # ct_env KONTEYNER KALIT
  docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$1" | sed -n "s/^$2=//p" | head -1
}
if [ -f "$BOT_ENV" ]; then
  say "Bot sozlamalari: $BOT_ENV (o'zgartirilmaydi)"
  BOT_DB_RAW="$(env_get DATABASE_URL "$BOT_ENV")"
  CHANNEL="$(env_get BASE_CHANNEL_ID "$BOT_ENV")"
else
  say "Bot sozlamalari ishlab turgan bot konteyneridan o'qilmoqda (o'zgartirilmaydi)"
  BOT_CT=""
  for c in $(docker ps -q); do
    if [ -n "$(ct_env "$c" BASE_CHANNEL_ID)" ]; then BOT_CT="$c"; break; fi
  done
  [ -n "$BOT_CT" ] || die "Bot topilmadi: $BOT_ENV yo'q va BASE_CHANNEL_ID'li konteyner ishlamayapti"
  ok "bot konteyneri: $(docker inspect -f '{{.Name}}' "$BOT_CT" | tr -d /)"
  BOT_DB_RAW="$(ct_env "$BOT_CT" DATABASE_URL)"
  CHANNEL="$(ct_env "$BOT_CT" BASE_CHANNEL_ID)"
fi
BOT_DB_RAW="${BOT_DB_RAW%\"}"; BOT_DB_RAW="${BOT_DB_RAW#\"}"
CHANNEL="${CHANNEL%\"}"; CHANNEL="${CHANNEL#\"}"
[ -n "$BOT_DB_RAW" ] || die "Bot sozlamalarida DATABASE_URL yo'q"
[[ "$CHANNEL" =~ ^-100[0-9]+$ ]] || die "Bot sozlamalarida BASE_CHANNEL_ID noto'g'ri: '$CHANNEL'"
env_set TG_BASE_CHANNEL_ID "$CHANNEL" "$ENV_FILE"
ok "baza kanal: $CHANNEL"

BOT_DB="$(clean_pg_url "$BOT_DB_RAW")"
DB_HOST="$(url_host "$BOT_DB")"

# Baza Docker konteyneri (masalan compose'dagi "postgres" servisi) bo'lsa — o'sha
# konteyner turgan tarmoqni topamiz: psql ham, ilova API'si ham shu tarmoqqa ulanadi.
find_db_net() { # find_db_net HOST -> tarmoq nomi
  local c name svc net aliases
  for c in $(docker ps -q); do
    name="$(docker inspect -f '{{.Name}}' "$c" | tr -d /)"
    svc="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.service"}}' "$c")"
    while IFS='=' read -r net aliases; do
      [ -n "$net" ] || continue
      if [ "$name" = "$1" ] || [ "$svc" = "$1" ] || [[ ",$aliases," == *",$1,"* ]]; then
        echo "$net"; return 0
      fi
    done < <(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}={{join $v.Aliases ","}}{{"\n"}}{{end}}' "$c")
  done
  return 1
}
DB_NET=""
PSQL_NET="host"
case "$DB_HOST" in
  localhost|127.0.0.1)
    warn "Bot bazasi hostda (localhost) — API konteyneri unga ulana olmasligi mumkin" ;;
  *)
    if ! getent hosts "$DB_HOST" >/dev/null 2>&1; then
      DB_NET="$(find_db_net "$DB_HOST" || true)"
      [ -n "$DB_NET" ] || die "Bot bazasi '$DB_HOST' — bunday konteyner/host topilmadi"
      PSQL_NET="$DB_NET"
      ok "bot bazasi Docker tarmog'ida: $DB_HOST ($DB_NET)"
    fi ;;
esac

# ---------- 4b. 80/443: o'z Caddy'miz yoki serverdagi mavjud Caddy ----------
# 443 ni boshqa Caddy konteyneri (masalan bot loyihasining sayti) band qilgan
# bo'lsa — o'z Caddy'mizni ko'tarmaymiz, API'ni o'sha Caddy tarmog'iga ulab,
# uning Caddyfile'iga faqat api./stream. bloklarini qo'shamiz.
PROXY_CT="" PROXY_NET="" PROXY_FILE=""
if ! "${COMPOSE[@]}" ps --status running --services 2>/dev/null | grep -qx caddy; then
  PROXY_CT="$(docker ps --filter publish=443 --format '{{.Names}}' | head -1)"
  if [ -n "$PROXY_CT" ]; then
    docker inspect -f '{{.Config.Image}}' "$PROXY_CT" | grep -q caddy \
      || die "443 ni '$PROXY_CT' konteyneri band qilgan (Caddy emas) — qo'lda sozlash kerak"
    PROXY_FILE="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/etc/caddy/Caddyfile"}}{{.Source}}{{end}}{{end}}' "$PROXY_CT")"
    PROXY_NET="$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{"\n"}}{{end}}' "$PROXY_CT" | head -1)"
    [ -n "$PROXY_FILE" ] && [ -f "$PROXY_FILE" ] \
      || die "'$PROXY_CT' Caddyfile'i fayl sifatida ulanmagan — qo'lda sozlash kerak"
    ok "mavjud Caddy ishlatiladi: $PROXY_CT ($PROXY_FILE, tarmoq $PROXY_NET)"
  else
    BUSY="$( (ss -Htlnp 2>/dev/null || true) | awk '$4 ~ /:(80|443)$/ {print $4, $6}')"
    [ -z "$BUSY" ] || die "80/443 port band (Docker emas):
$BUSY
Serverdagi veb-serverni to'xtatmaymiz — qo'lda sozlash kerak."
  fi
fi

# API'ni kerakli Docker tarmoqlariga ulash (compose qo'shimcha fayli, git'ga kirmaydi)
NET_OVERRIDE="$DEPLOY_DIR/.botnet.yml"
EXT_NETS=()
for n in "$DB_NET" "$PROXY_NET"; do
  if [ -n "$n" ] && [[ " ${EXT_NETS[*]} " != *" $n "* ]]; then EXT_NETS+=("$n"); fi
done
if [ "${#EXT_NETS[@]}" -gt 0 ]; then
  {
    echo "services:"; echo "  api:"; echo "    networks:"; echo "      default: {}"
    for i in "${!EXT_NETS[@]}"; do
      echo "      ext$i:"; echo "        aliases: [kino-makoni-api]"
    done
    echo "networks:"
    for i in "${!EXT_NETS[@]}"; do
      echo "  ext$i:"; echo "    external: true"; echo "    name: ${EXT_NETS[$i]}"
    done
  } > "$NET_OVERRIDE"
  COMPOSE+=(-f "$NET_OVERRIDE")
  ok "API tarmoqlari: ${EXT_NETS[*]} (alias kino-makoni-api)"
else
  rm -f "$NET_OVERRIDE"
fi

# ---------- 5. Bazalar: o'qish roli + alohida ilova bazasi ----------
say "Postgres sozlanmoqda (psql: $PG_IMAGE)"
docker pull -q "$PG_IMAGE" >/dev/null

CUR_READER="$(env_get BOT_DATABASE_URL "$ENV_FILE")"
if [[ "$CUR_READER" == *"$READER_ROLE"* ]] && [[ "$CUR_READER" != *kuchli-parol* ]] \
   && echo "SELECT 1 FROM movies LIMIT 1;" | psql_run "$(clean_pg_url "$CUR_READER")" >/dev/null 2>&1; then
  ok "o'qish roli allaqachon ishlayapti"
else
  READER_PW="$(rand 32)"
  if psql_run "$BOT_DB" -v pw="$READER_PW" -v role="$READER_ROLE" <<'SQL'
SELECT NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'role') AS need_create \gset
\if :need_create
CREATE ROLE :"role" LOGIN PASSWORD :'pw';
\else
ALTER ROLE :"role" WITH LOGIN PASSWORD :'pw';
\endif
SELECT current_database() AS dbname \gset
GRANT CONNECT ON DATABASE :"dbname" TO :"role";
GRANT USAGE ON SCHEMA public TO :"role";
GRANT SELECT ON TABLE public.movies, public.serials, public.seasons, public.episodes TO :"role";
ALTER ROLE :"role" SET default_transaction_read_only = on;
SQL
  then
    DBNAME="$(python3 -c 'import sys;from urllib.parse import urlsplit;print(urlsplit(sys.argv[1]).path.lstrip("/"))' "$BOT_DB")"
    env_set BOT_DATABASE_URL "$(rewrite_pg_url "$BOT_DB" "$READER_ROLE" "$READER_PW" "$DBNAME" 0)" "$ENV_FILE"
    ok "o'qish roli: $READER_ROLE (faqat SELECT: movies, serials, seasons, episodes)"
  else
    warn "o'qish rolini yaratib bo'lmadi — bot URL'i ishlatiladi (sinxronlash baribir READ ONLY tranzaksiyada)"
    env_set BOT_DATABASE_URL "$BOT_DB" "$ENV_FILE"
  fi
fi

CUR_APP="$(env_get DATABASE_URL "$ENV_FILE")"
if [[ "$CUR_APP" == postgresql+asyncpg://"$APP_ROLE":* ]] || [[ "$CUR_APP" == sqlite* ]]; then
  ok "ilova bazasi allaqachon sozlangan"
else
  APP_PW="$(rand 32)"
  if psql_run "$BOT_DB" -v pw="$APP_PW" -v role="$APP_ROLE" -v db="$APP_DB" <<'SQL'
SELECT NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'role') AS need_create \gset
\if :need_create
CREATE ROLE :"role" LOGIN PASSWORD :'pw';
\else
ALTER ROLE :"role" WITH LOGIN PASSWORD :'pw';
\endif
GRANT :"role" TO CURRENT_USER;
SELECT NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'db') AS need_db \gset
\if :need_db
CREATE DATABASE :"db" OWNER :"role";
\endif
SQL
  then
    env_set DATABASE_URL "$(rewrite_pg_url "$BOT_DB" "$APP_ROLE" "$APP_PW" "$APP_DB" 1)" "$ENV_FILE"
    ok "ilova bazasi: $APP_DB (egasi $APP_ROLE, botnikidan alohida)"
  else
    warn "alohida Postgres bazasini yaratib bo'lmadi — SQLite ishlatiladi (/data hajmida saqlanadi)"
    env_set DATABASE_URL "sqlite+aiosqlite:////data/kino_makoni.db" "$ENV_FILE"
  fi
fi

# ---------- 6. Ishga tushirish ----------
if [ -n "$PROXY_CT" ]; then
  say "API ishga tushirilmoqda (birinchi build 3-6 daqiqa; Caddy — mavjud $PROXY_CT)"
  "${COMPOSE[@]}" up -d --build --remove-orphans api
else
  say "API va Caddy ishga tushirilmoqda (birinchi build 3-6 daqiqa)"
  "${COMPOSE[@]}" up -d --build --remove-orphans
fi

say "Sog'liq tekshiruvi"
HEALTH=""
for _ in $(seq 1 45); do
  HEALTH="$(curl -fsS -m 3 http://127.0.0.1:8000/health 2>/dev/null || true)"
  [ -n "$HEALTH" ] && break
  sleep 2
done
if [ -z "$HEALTH" ]; then
  "${COMPOSE[@]}" logs --tail 60 api || true
  die "API javob bermadi (loglar yuqorida)"
fi
ok "health: $HEALTH"

# ---------- 6b. Mavjud Caddy'ga api./stream. bloklari ----------
if [ -n "$PROXY_CT" ]; then
  say "Caddy ($PROXY_CT): api.$DOMAIN va stream.$DOMAIN qo'shilmoqda"
  BAK="$PROXY_FILE.bak-kino-makoni-$(date +%Y%m%d-%H%M%S)"
  cp -p "$PROXY_FILE" "$BAK"
  # Fayl joyida (inode saqlanib) yoziladi — konteynerga bitta fayl bind-mount qilingan
  python3 - "$PROXY_FILE" "$DOMAIN" <<'PY'
import re, sys
path, domain = sys.argv[1], sys.argv[2]
begin = "# >>> kino-makoni (bootstrap.sh qo'shgan — Kino Makoni iOS ilovasi API) >>>"
end = "# <<< kino-makoni <<<"
block = f"""{begin}
api.{domain} {{
	encode gzip
	reverse_proxy kino-makoni-api:8000
}}

stream.{domain} {{
	reverse_proxy kino-makoni-api:8000 {{
		flush_interval -1
		transport http {{
			read_timeout 3600s
			write_timeout 3600s
			dial_timeout 5s
			response_header_timeout 60s
		}}
	}}
}}
{end}
"""
with open(path, "r+") as f:
    text = f.read()
    text = re.sub(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", "", text, flags=re.S).rstrip("\n")
    f.seek(0); f.write(text + "\n\n" + block); f.truncate()
PY
  if docker exec "$PROXY_CT" caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/tmp/km_caddy.log 2>&1; then
    docker exec "$PROXY_CT" caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile >>/tmp/km_caddy.log 2>&1 \
      || { cat "$BAK" > "$PROXY_FILE"; tail -20 /tmp/km_caddy.log; die "caddy reload xato — Caddyfile qaytarildi"; }
    ok "Caddy yangilandi (zaxira: $BAK)"
  else
    cat "$BAK" > "$PROXY_FILE"
    tail -20 /tmp/km_caddy.log
    die "Caddyfile tekshiruvdan o'tmadi — o'zgarish qaytarildi"
  fi
  for _ in $(seq 1 20); do
    code="$(curl -s -o /dev/null -w '%{http_code}' -m 5 --resolve "api.$DOMAIN:443:127.0.0.1" "https://api.$DOMAIN/health" || true)"
    [ "$code" = 200 ] && break
    sleep 3
  done
  if [ "${code:-}" = 200 ]; then ok "https://api.$DOMAIN/health — HTTPS ishlayapti"
  else warn "api.$DOMAIN HTTPS hali tayyor emas (sertifikat olinmoqda yoki DNS) — birozdan so'ng tekshiring"; fi
fi

# ---------- 7. Telegram tekshiruvi ----------
say "Telegram (yordamchi bot) tekshirilmoqda"
MSG="$(echo 'SELECT "baseMsgId" FROM movies WHERE "baseMsgId" IS NOT NULL ORDER BY id DESC LIMIT 1;' \
  | psql_run "$(clean_pg_url "$(env_get BOT_DATABASE_URL "$ENV_FILE")")" -tA 2>/dev/null | tr -d '[:space:]' || true)"
if [ -n "$MSG" ]; then
  "${COMPOSE[@]}" exec -T api python scripts/tg_check.py --msg "$MSG" --download-first-mb 4 \
    || warn "tg_check muvaffaqiyatsiz — yuqoridagi maslahatlarga qarang"
else
  "${COMPOSE[@]}" exec -T api python scripts/tg_check.py || warn "tg_check muvaffaqiyatsiz"
fi

# ---------- 8. DNS va yakun ----------
say "DNS holati"
IP="$(curl -fsS -m 5 https://checkip.amazonaws.com 2>/dev/null | tr -d '[:space:]' || true)"
for host in "api.$DOMAIN" "stream.$DOMAIN"; do
  got="$( (getent ahostsv4 "$host" 2>/dev/null || true) | awk 'NR==1{print $1}')"
  if [ -z "$got" ]; then
    warn "$host — DNS yozuvi yo'q. A yozuv qo'shing: $host → $IP"
  elif [ "$got" = "$IP" ]; then
    ok "$host → $got"
  else
    warn "$host → $got (bu server IP'si emas: $IP). Cloudflare proxy yoqilgan bo'lsa bu normal (faqat api.)"
  fi
done

IP_SHOW="${IP:-<EC2 IP>}"
cat <<EOF

────────────────────────────────────────────────────────────
 Tayyor. Server IP: $IP_SHOW
  • DNS: api.$DOMAIN va stream.$DOMAIN → A → $IP_SHOW
    (Cloudflare'da stream. — faqat DNS, kulrang bulut)
  • EC2 Security group: 80 va 443 portlar ochiq bo'lishi shart
  • Tekshirish: curl https://api.$DOMAIN/health
  • Loglar:     ${COMPOSE[*]} logs -f api
────────────────────────────────────────────────────────────
EOF
