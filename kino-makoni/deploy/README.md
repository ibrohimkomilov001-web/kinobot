# Kino Makoni — deploy (EC2)

Bu katalog `kino-makoni-app` compose loyihasini tashkil qiladi — bot
(`~/KINO_MAKON`, `kino-makon` repo)dan **butunlay mustaqil**, bir xil EC2
instansda ishlaydi. To'liq qadamlar: [`../docs/DEPLOY.md`](../docs/DEPLOY.md).

## Fayllar

| Fayl | Vazifasi |
|---|---|
| `docker-compose.yml` | `api` (FastAPI, `../backend`dan build) + `caddy` (TLS/reverse proxy) |
| `Caddyfile` | `API_DOMAIN` va `STREAM_DOMAIN` uchun reverse proxy sozlamalari |
| `.env` | **Git'ga tushmaydi.** `../backend/.env.example` asosida to'ldiriladi; EC2'da `KINO_MAKONI_DOTENV` GitHub Secret'idan avtomatik yoziladi (`kino-makoni-api-deploy.yml`) |

## Ishga tushirish (EC2'da, avtomatik)

`kino-makoni-api-deploy.yml` GitHub Actions workflow'i orqali (`main`'ga
push yoki qo'lda ishga tushirish). Sekretlar sozlangan bo'lishi kerak —
`../docs/DEPLOY.md`ga qarang.

## Qo'lda ishga tushirish / lokal tekshirish

```bash
cd kino-makoni/deploy
cp ../backend/.env.example .env   # va qiymatlarni to'ldiring
docker compose -p kino-makoni-app -f docker-compose.yml up -d --build
docker compose -p kino-makoni-app -f docker-compose.yml ps
curl -fsS http://127.0.0.1:8000/health
```

To'xtatish (FAQAT shu loyiha, bot'ga tegmaydi):

```bash
docker compose -p kino-makoni-app -f docker-compose.yml down
```

## Yordamchi botni tekshirish

Skript backend ichida (`../backend/scripts/tg_check.py`) — konteynerda ishga tushiriladi:

```bash
docker compose -p kino-makoni-app -f docker-compose.yml \
  exec api python scripts/tg_check.py --msg <baseMsgId> --download-first-mb 16
```

## Eslatmalar

- `api` xizmati faqat `127.0.0.1:8000`ga bog'lanadi — tashqi trafik faqat
  Caddy orqali (80/443) o'tadi.
- EC2 xavfsizlik guruhida 80 va 443 portlari ochiq bo'lishi SHART (Caddy
  Let's Encrypt sertifikat olishi uchun).
- `STREAM_DOMAIN` Cloudflare'da **DNS only** (kulrang bulut) bo'lishi kerak —
  sabab `Caddyfile`dagi izohda va `../docs/DEPLOY.md`da.
- Ushbu compose loyihasi bot loyihasidan (`~/KINO_MAKON`, `docker compose`
  ismisiz/standart nom bilan) `-p kino-makoni-app` bayrog'i bilan ajratiladi
  — ikkisi bir xil `docker compose down` buyrug'i ostida QOLMAYDI.
