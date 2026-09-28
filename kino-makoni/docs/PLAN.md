# Kino Makoni — iOS ilova rejasi

> Holat: **1-bosqich (MVP) ishlanmoqda.** Sana: 2026-09-28.

## Qabul qilingan qarorlar

| Mavzu | Qaror | Sabab |
|---|---|---|
| iOS frontend | **SwiftUI**, iOS 26+, haqiqiy Liquid Glass (`.glassEffect`, `.buttonStyle(.glass)`, `Tab(role: .search)`) | Python UI kutubxonalari Liquid Glass'ni chiza olmaydi |
| Backend | **Python 3.12 + FastAPI**, SQLAlchemy, Alembic, Telethon | Talab: backend Python'da |
| Mavzu | Faqat tungi (dark) mavzu, aksent — logodagi tilla `#E8C166` (gradient `#F8E4A9` → `#B7842A`) | Logo ranglariga mos |
| Video manbai | Botning **maxfiy baza kanali**dan MTProto orqali stream (HTTP Range) | Kontent tayyor; keyinroq admin panel → R2 |
| Bot bilan aloqa | Bot bazasini **faqat o'qish** (read-only rol) + **alohida yordamchi bot** | Ilova botga hech narsa yozmaydi, bot kodi o'zgarmaydi |
| Server | AWS EC2 (botniki bilan bir xil server, **alohida** Docker loyiha) + Caddy (HTTPS) | Mavjud infratuzilma |
| CDN / fayllar | Cloudflare DNS; keyingi bosqichda Cloudflare R2 (trafik bepul) | AWS'da video trafigi pullik |
| Build | Codemagic → imzosiz `.ipa` → Sideloadly bilan o'rnatish | Tayyor jarayon |
| Kompilyatsiya tekshiruvi | GitHub Actions macOS runner (imzosiz build) | Har push'da Swift kodi tekshiriladi |

## Arxitektura

```
 iPhone (SwiftUI, Liquid Glass)
   │  JSON: https://api.<domen>/v1/...        (Cloudflare proxy)
   │  Video: https://stream.<domen>/v1/stream/<imzolangan token>/video.mp4
   ▼
 EC2 ── Caddy (HTTPS) ── kino-makoni-api (FastAPI, 1 worker)
                             │  ├─ ilova bazasi (Neon, ALOHIDA DB): foydalanuvchi, sevimlilar, progress, katalog nusxasi
                             │  ├─ bot bazasi (Neon, READ-ONLY rol) → har 5 daqiqada katalog sinxronlash
                             │  └─ Telethon (yordamchi bot) → maxfiy baza kanal → video baytlari (Range)
 EC2 ── kinobot (mavjud bot, TEGILMAYDI)
```

Ilova qurilma bo'yicha anonim akkaunt oladi (`POST /v1/auth/device`) — ro'yxatdan
o'tish shart emas. Stream URL'lari HMAC bilan imzolanadi va 6 soatda eskiradi.

## Repo tuzilishi

```
codemagic.yaml                     # iOS build (Codemagic talabi: repo ildizida)
.github/workflows/kino-makoni-*.yml
kino-makoni/
├── docs/        PLAN.md, API.md (kontrakt), DEPLOY.md, SIDELOAD.md
├── backend/     FastAPI (app/core, app/api/v1, app/services, app/streaming, tests)
├── ios/         project.yml (XcodeGen) + KinoMakoni/ (SwiftUI)
├── deploy/      docker-compose.yml + Caddyfile (EC2 uchun)
└── branding/    logo va ikonka generatori
```

Repo ildizidagi eski bot fayllari (`bot.py`, `handlers/` …) bu ishda o'zgartirilmaydi.

## Bosqichlar

### 1-bosqich — MVP (hozir)
- [x] Arxitektura, API kontrakti (`docs/API.md`), umumiy modullar (config, imzolash)
- [ ] Backend: katalog sinxronlash, qidiruv (kirill/lotin), bosh sahifa, sevimlilar, progress, playback
- [ ] Stream: Telegram MTProto → HTTP Range (AVPlayer uchun), thumbnail'lar
- [ ] iOS: Bosh sahifa, Qidiruv, Saqlanganlar, Profil, Batafsil, Pleyer (PiP), demo rejim
- [x] Codemagic + GitHub Actions: imzosiz `.ipa`
- [x] Deploy hujjatlari (EC2 + Caddy + Cloudflare), logo va ikonka

### 2-bosqich — Ishga tushirish
- Yordamchi bot, `api_id/api_hash`, read-only rol, ilova bazasi, domen sozlash
- EC2'ga deploy, haqiqiy kontent bilan sinov, Sideloadly orqali o'rnatish
- Icon Composer bilan qatlamli Liquid Glass ikonka (logo asosida)
- TMDB posterlari (ixtiyoriy kalit)

### 3-bosqich — Admin panel va R2 (keyinga surilgan)
- Python web admin panel: kino/serial qo'shish, tahrirlash, poster yuklash
- Videolarni Cloudflare R2'ga yuklash (HLS ga o'girish — ffmpeg)
- Mashhur kinolarni Telegram'dan R2'ga keshlash (EC2 trafigini kamaytirish)

### 4-bosqich — Kengaytmalar
- Premium (ilova ichida), Telegram akkaunt bilan bog'lash
- Push bildirishnomalar, oflayn yuklab olish, tavsiyalar

## Foydalanuvchi bajarishi kerak bo'lgan ishlar
1. ~~Logo~~ — qabul qilindi (`branding/logo.png`, 512×512). Iloji bo'lsa 1024×1024 PNG asl nusxasini ham yuboring — ikonka tiniqroq chiqadi.
2. @BotFather'da **yangi yordamchi bot** → botning maxfiy baza kanaliga **admin** qilish.
3. https://my.telegram.org → `api_id`, `api_hash`.
4. Neon: bot bazasiga read-only rol + ilova uchun alohida baza (SQL — `docs/DEPLOY.md`).
5. Domen (Cloudflare): `api.` va `stream.` subdomenlar → EC2 IP.
6. GitHub Secrets (shu repo): `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`, `KINO_MAKONI_DOTENV`.
7. Codemagic: variable group `kino_makoni` → `API_BASE_URL`.

## Xavflar va cheklovlar
- **MKV fayllar** AVPlayer'da ijro etilmaydi (faqat MP4/MOV/HLS). Kanalda MKV bo'lsa — 3-bosqichda o'girish.
- **Trafik narxi**: video Telegram → EC2 → foydalanuvchi oqadi; AWS 100 GB/oy bepul, keyin ~$0.09/GB.
- **t3.micro** (1 GB RAM): bot + API + Caddy sig'adi, lekin 1 GB swap tavsiya etiladi.
- **Sideload**: bepul Apple ID bilan ilova 7 kunda qayta imzolanishi kerak.
- Premium kinolar ilovada hozircha qulflangan (`PREMIUM_ENFORCED=true`).
