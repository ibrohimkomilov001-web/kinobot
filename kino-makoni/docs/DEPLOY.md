# Kino Makoni — Backend'ni EC2'ga deploy qilish

Ushbu hujjat `kino-makoni/backend` (FastAPI) ni bot bilan bir xil AWS EC2
instansiga, lekin **butunlay alohida** Docker Compose loyihasi sifatida
o'rnatishni tushuntiradi. Bot (`kino-makon` repo, `~/KINO_MAKON`) bunga
tegilmaydi va ishlashda davom etadi.

> **Joriy holat (2026-09-28):** API bot serverida (`kinobot`, i-002a6503b1aa8cf4c,
> eu-central-1, 3.127.203.19) `/opt/kino-makoni` da, compose loyihasi
> `kino-makoni-app`. Bot loyihasi (`/app`: bot, web, postgres, caddy) o'zgartirilmagan —
> faqat `/app/Caddyfile` oxiriga `# >>> kino-makoni` markerli api./stream. bloklari
> qo'shilgan (zaxiralar: `/app/Caddyfile.bak-kino-makoni-*`). `/app` qayta deploy
> qilinib Caddyfile ustidan yozilsa — `bootstrap.sh`ni qayta ishga tushiring, bloklar
> qayta qo'shiladi. Server AWS SSM orqali boshqariladi (`kinobot-ec2-role` ga
> `AmazonSSMManagedInstanceCore` biriktirilgan).

## 1. Arxitektura

```
                         Cloudflare DNS
              ┌───────────────────────────────────┐
              │  api.<domain>      stream.<domain> │
              │  (Proxied,          (DNS only,     │
              │   turuncha bulut)    kulrang bulut) │
              └──────────┬──────────────┬───────────┘
                         │              │
                         ▼              ▼
              ┌─────────────────────────────────────────┐
              │  AWS EC2 (t3.micro, Ubuntu 24.04)        │
              │                                           │
              │  ~/KINO_MAKON            ~/KINO_MAKONI_APP│
              │  (bot, alohida            (bu loyiha,     │
              │   compose loyihasi,        "-p kino-makoni│
              │   TEGILMAYDI)              -app")         │
              │                                           │
              │                 ┌─────────────────────┐   │
              │                 │ caddy:2-alpine      │   │
              │                 │  :80 / :443         │   │
              │                 └──────────┬──────────┘   │
              │                            │ reverse_proxy  │
              │                            ▼               │
              │                 ┌─────────────────────┐   │
              │                 │ api (FastAPI)        │   │
              │                 │  127.0.0.1:8000      │   │
              │                 │  volume: /data        │   │
              │                 └───┬──────────────┬───┘   │
              └─────────────────────┼──────────────┼────────┘
                                    │              │
                    read-only SQL  │              │ MTProto (yordamchi bot)
                                    ▼              ▼
                        ┌──────────────────┐  ┌─────────────────────┐
                        │ Neon — bot bazasi │  │ Telegram baza kanali │
                        │ (FAQAT O'QISH)     │  │ (video manbai)       │
                        └──────────────────┘  └─────────────────────┘
                                    ▲
                                    │ o'z bazasi (alohida)
                        ┌──────────────────┐
                        │ Neon — ilova bazasi│
                        └──────────────────┘
```

Video oqimi: **Telegram → EC2 (api) → foydalanuvchi (AVPlayer)**. Bu degani
har bir tomosha AWS'dan chiquvchi trafik (egress) sarflaydi — pastga, "Narx"
bo'limiga qarang.

## 2. Oldindan qilinishi kerak bo'lgan ishlar

### (a) Yangi yordamchi bot (@BotFather)

1. Telegram'da **@BotFather** ga yozing → `/newbot` → nom va username bering
   (masalan `KinoMakoniStreamBot`). Tokenni saqlab qo'ying — bu
   `TG_HELPER_BOT_TOKEN`.
2. **MUHIM**: bu — YANGI, alohida bot. Asosiy Telegram bot tokeningizni
   bu yerda ISHLATMANG.
3. Bu botni bot bazasi kanaliga (video fayllar saqlanadigan maxfiy kanal)
   **ADMIN** sifatida qo'shing (kanal → Administrators → Add Admin →
   yangi bot). Admin bo'lmasa video fayllarni o'qiy olmaydi.
4. Tekshirish: `kino-makoni/backend/scripts/tg_check.py` (pastdagi "Tekshirish" bo'limiga qarang).

### (b) Telegram API ID/Hash (my.telegram.org)

1. https://my.telegram.org → shaxsiy raqamingiz bilan kiring → **API
   development tools** → yangi ilova yarating (nom ixtiyoriy).
2. `api_id` va `api_hash`ni saqlang — bular `TG_API_ID` / `TG_API_HASH`.
   Bular yordamchi bot MTProto (Telethon) orqali ulanishi uchun kerak
   (Bot API katta fayllarni streaming uchun yetarli emas).

### (c) Postgres: bot bazasidan FAQAT O'QISH roli + ilova uchun ALOHIDA baza

Botning Neon loyihasida (Neon dashboard → SQL Editor):

```sql
CREATE ROLE kino_makoni_ro WITH LOGIN PASSWORD 'kuchli-parol-shu-yerga';
GRANT CONNECT ON DATABASE <bot_baza_nomi> TO kino_makoni_ro;
GRANT USAGE ON SCHEMA public TO kino_makoni_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO kino_makoni_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO kino_makoni_ro;
```

Shu rol bilan ulanish satrini yig'ing — bu `BOT_DATABASE_URL`
(masalan `postgresql://kino_makoni_ro:...@<bot-host>/<bot_baza_nomi>`).

Ilova o'zining ma'lumotlari (foydalanuvchilar, sevimlilar, progress) uchun
**Neon'da YANGI, alohida loyiha/baza** yarating (bot bazasiga aralashmasin):
Neon dashboard → New Project → nomi masalan `kino-makoni-app`. Ulanish
satri — `DATABASE_URL`.

### (d) Cloudflare domen

Domeningiz Cloudflare'da bo'lishi kerak. DNS → Records:

| Turi | Nomi | Qiymati | Proxy holati |
|---|---|---|---|
| A | `api` (`api.<domen>`) | EC2 Elastic IP | **Proxied** (turuncha bulut) |
| A | `stream` (`stream.<domen>`) | EC2 Elastic IP | **DNS only** (kulrang bulut) |

`stream.<domen>` ni Proxied qilmang — sabab `kino-makoni/deploy/Caddyfile`
faylidagi izohda: video oqimi katta hajmda va uzoq davom etadi, Cloudflare
bepul/Pro tarifining foydalanish shartlari CDN orqali doimiy video
translatsiyani cheklaydi. "DNS only" bilan AVPlayer'ning Range so'rovlari
to'g'ridan-to'g'ri EC2'dagi Caddy'ga boradi.

### (e) EC2 xavfsizlik guruhi + swap

Xavfsizlik guruhida (Security group) qo'shing: **80** va **443** (TCP,
`0.0.0.0/0`), agar `22` (SSH) hali ochiq bo'lmasa — o'z IP'ingizga.

`t3.micro`da faqat 1 GB RAM bor — build paytida (ayniqsa Docker build)
xotira yetishmasligi mumkin. 1 GB swap qo'shing:

```bash
ssh -i kinobot.pem ubuntu@<EC2_HOST>
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h   # tekshirish
```

### (f) GitHub Secrets (SHU repo — `ibrohimkomilov001-web/kinobot`)

Repo → **Settings → Secrets and variables → Actions → New repository
secret**:

| Nomi | Qiymati |
|---|---|
| `EC2_HOST` | EC2 public IP yoki Elastic IP |
| `EC2_USER` | odatda `ubuntu` |
| `EC2_SSH_KEY` | `.pem` faylning TO'LIQ matni |
| `KINO_MAKONI_DOTENV` | `kino-makoni/deploy/.env` ning TO'LIQ matni (`kino-makoni/backend/.env.example` asosida to'ldirilgan) |

> Agar bot uchun `EC2_HOST`/`EC2_USER`/`EC2_SSH_KEY` allaqachon boshqa
> repo'da (`kino-makon`) sozlangan bo'lsa ham, ular alohida repo — shu
> qiymatlarni **shu repo'ga QAYTA** kiritishingiz kerak (GitHub sekretlar
> repo bo'yicha alohida saqlanadi). `KINO_MAKONI_DOTENV` esa bot'ning
> `DOTENV`'idan butunlay boshqa (boshqa bot tokeni, boshqa baza).

### (g) Deploy workflow'ni ishga tushirish

Sekretlar sozlangach: GitHub → **Actions → Kino Makoni API Deploy → Run
workflow** (yoki `kino-makoni/backend/**`/`kino-makoni/deploy/**`ga `main`
orqali push qiling). Workflow EC2'ga faqat `kino-makoni/` katalogini
sparse-checkout qiladi, `.env`ni yozadi va
`docker compose -p kino-makoni-app up -d --build` ishga tushiradi.

#### AWS CloudShell orqali (`.pem` kalitsiz)

AWS Console → CloudShell (istalgan region — server barcha regionlardan topiladi):

```bash
curl -fsSL https://raw.githubusercontent.com/ibrohimkomilov001-web/kinobot/refs/heads/claude/eager-lovelace-0db0j8/kino-makoni/deploy/cloudshell.sh -o cs.sh
TG_API_ID=... TG_API_HASH=... TG_HELPER_BOT_TOKEN=... bash cs.sh
```

`cloudshell.sh` akkaunt ID'sini chiqaradi, bot serverini IP bo'yicha topadi,
80/443 ni ochadi, EC2 Instance Connect bilan (vaqtinchalik 22-port faqat
CloudShell IP'siga) serverga kirib `bootstrap.sh`ni ishga tushiradi va
oxirida vaqtinchalik qoidani o'chiradi.

#### Eng oson yo'l: `bootstrap.sh` (bitta buyruq)

EC2'da (bot ishlayotgan server) bir marta:

```bash
curl -fsSL https://raw.githubusercontent.com/ibrohimkomilov001-web/kinobot/refs/heads/claude/eager-lovelace-0db0j8/kino-makoni/deploy/bootstrap.sh -o bootstrap.sh
TG_API_ID=... TG_API_HASH=... TG_HELPER_BOT_TOKEN=... DOMAIN=kinomakoni.uz bash bootstrap.sh
```

Skript swap, kod, `.env`, bot bazasida o'qish roli + alohida ilova bazasi
(`~/KINO_MAKON/.env`dagi `DATABASE_URL`/`BASE_CHANNEL_ID` faqat o'qiladi),
Docker, sog'liq va Telegram tekshiruvini bajaradi; oxirida DNS holatini
ko'rsatadi. Qayta ishga tushirish xavfsiz (yangilash uchun ham shu skript).
80/443 boshqa veb-server band qilgan bo'lsa hech narsaga tegmay to'xtaydi.

#### Qo'lda deploy (GitHub Actions ishlamasa)

Akkauntda Actions bloklangan bo'lsa (job'lar bir necha soniyada log'siz
yiqiladi — odatda billing sababli), EC2'da to'g'ridan-to'g'ri:

```bash
ssh -i kinobot.pem ubuntu@<EC2_HOST>

# Birinchi marta: faqat kino-makoni/ papkasini olish (bot papkasiga tegmaydi)
git clone --filter=blob:none --sparse -b claude/eager-lovelace-0db0j8 \
  https://github.com/ibrohimkomilov001-web/kinobot.git ~/KINO_MAKONI_APP
cd ~/KINO_MAKONI_APP && git sparse-checkout set kino-makoni

# .env ni joylash (tayyor faylni shu yerga ko'chiring), keyin:
chmod 600 kino-makoni/deploy/.env
docker compose -p kino-makoni-app -f kino-makoni/deploy/docker-compose.yml up -d --build

# Keyingi yangilanishlar:
cd ~/KINO_MAKONI_APP && git pull --ff-only && \
  docker compose -p kino-makoni-app -f kino-makoni/deploy/docker-compose.yml up -d --build
```

### (h) Tekshirish

```bash
curl -s https://api.<domen>/health
# { "status": "ok", "db": true, "telegram": true, ... }

curl -I "https://stream.<domen>/v1/stream/<token>/video.mp4"
# 200 yoki 206 (imzolangan token bilan)
```

Yordamchi bot sozlamalarini tekshirish — EC2'da, ishlab turgan konteyner ichida
(`<id>` — bot bazasidagi biror kinoning `baseMsgId` qiymati):

```bash
cd ~/KINO_MAKONI_APP
docker compose -p kino-makoni-app -f kino-makoni/deploy/docker-compose.yml \
  exec api python scripts/tg_check.py --msg <id> --download-first-mb 16
```

Skript login, kanalga kirish, video formati (MKV/WEBM ogohlantirishi, MP4
"fast start") va yuklab olish tezligini tekshiradi.

### (i) Cloudflare R2 (keyingi bosqich — admin panel)

Admin panel orqali yuklash boshlanganda: Cloudflare dashboard → R2 → Create
bucket (masalan `kino-makoni-media`). Hozircha `kino-makoni/backend`da
`R2_*` o'zgaruvchilar bo'sh qoldiriladi — ular faqat keyingi bosqichda
ishlatiladi (pastga, "Narx" bo'limiga qarang).

## 3. Narx haqida eslatma (MUHIM)

- AWS'dan chiquvchi trafik (egress): oyiga **100 GB bepul**, undan keyin
  **~$0.09/GB**.
- Video baytlari **Telegram → EC2 → foydalanuvchi** yo'nalishida oqadi —
  demak har bir tomosha shu egress'ni sarflaydi. Masalan 2 soatlik, 1080p
  film ≈ 1.5–2 GB — 50 marta tomosha qilinsa oyiga ≈ 75–100 GB (bepul
  chegaraga yaqin).
- **Reja**: keyingi bosqichda mashhur nomlarni Cloudflare R2'ga keshlab
  qo'yish (R2'dan chiquvchi trafik BEPUL) — shunda faqat birinchi
  yuklashgina AWS orqali o'tadi, qolganlari R2'dan. Hozircha bu amalga
  oshirilmagan, shuning uchun ko'p foydalanuvchi bo'lsa AWS billing'ni
  kuzatib turing.

## 4. Xotira byudjeti (`t3.micro`, 1 GB RAM)

| Xizmat | `mem_limit` | Izoh |
|---|---|---|
| `api` (FastAPI + 1 uvicorn worker) | ~300m | Telethon sessiyasi + so'rovlar shu ichida |
| `caddy` | ~64m | Faqat reverse proxy, statik fayl saqlamaydi |
| Bot (`~/KINO_MAKON`, alohida) | — | O'z compose loyihasi, shu hisobga kirmaydi |
| Ubuntu + Docker + boshqa | ~300–400m | |
| **Jami taxminiy** | ~700–800m / 1 GB + 1 GB swap | Zichlashsa swap yordam beradi (2(e)ga qarang) |

Agar xotira doim tugab qolsa: instansni `t3.small` (2 GB) ga ko'tarish eng
oson yechim (Free Tier tugagach oyiga qo'shimcha ~$15).
