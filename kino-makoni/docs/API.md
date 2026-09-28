# Kino Makoni — API kontrakti (v1)

Bu hujjat iOS ilova va Python backend o'rtasidagi **yagona manba**. Ikki tomon
ham shu shakllarga amal qiladi; o'zgarish kerak bo'lsa avval shu fayl yangilanadi.

- Asos URL: `API_PUBLIC_BASE_URL` (masalan `https://api.kinomakoni.uz`)
- Barcha JSON maydonlar `snake_case`. Vaqtlar ISO-8601 UTC (`2026-09-28T10:00:00Z`).
- `null` bo'lishi mumkin bo'lgan maydonlar `?` bilan belgilangan.
- Xato javobi har doim:
  ```json
  { "error": { "code": "not_found", "message": "Kino topilmadi" } }
  ```
  Kodlar: `unauthorized` (401), `forbidden` (403), `premium_required` (403),
  `not_found` (404), `unavailable` (409), `validation_error` (422),
  `rate_limited` (429), `internal` (500).

## Autentifikatsiya

Ro'yxatdan o'tish yo'q — har bir qurilma anonim "mehmon" akkaunt oladi.
`device_id` ilova birinchi ochilganda yaratiladi va Keychain'da saqlanadi.

### `POST /v1/auth/device`
Tokensiz. Bir xil `device_id` har doim bir xil foydalanuvchini qaytaradi.
```json
// so'rov
{ "device_id": "8F1C...-UUID", "platform": "ios", "app_version": "1.0.0" }
// javob 200
{
  "access_token": "<JWT HS256, sub=user_id>",
  "token_type": "bearer",
  "expires_in": 2592000,
  "user": { "id": 42, "created_at": "2026-09-28T10:00:00Z" }
}
```
Qolgan barcha `/v1/*` endpointlar `Authorization: Bearer <token>` talab qiladi
(`/v1/stream/*`, `/v1/thumb/*` va `/health` bundan mustasno — ular imzolangan URL
yoki ochiq). Token eskirsa 401 → ilova `/v1/auth/device` ni qayta chaqiradi.

## Obyektlar

### `TitleCard`
```json
{
  "id": 17,                      // ilova bazasidagi ID (bot ID'si EMAS)
  "kind": "movie",               // "movie" | "serial"
  "title": "Qasoskorlar: Final",
  "year": 2019,                  // ?
  "genres": ["Jangari", "Fantastika"],
  "poster_url": "https://...",   // ? vertikal 2:3
  "backdrop_url": "https://...", // ? gorizontal 16:9
  "is_premium": false,
  "quality": "1080p",            // ?
  "duration_sec": 10860          // ? (serial uchun null)
}
```

### `TitleDetail` = `TitleCard` + quyidagilar
```json
{
  "code": 1234,                  // botdagi kino kodi (ko'rsatish uchun)
  "description": "…",            // ? caption'dan tozalangan matn
  "language": "O'zbek tilida",   // ?
  "views": 15230,
  "is_favorite": false,
  "is_available": true,          // stream manbasi bormi
  "progress": {                  // ? oxirgi ko'rish holati
    "episode_id": null,          // ? serial bo'lsa qaysi qism
    "position_sec": 1200,
    "duration_sec": 10860
  },
  "seasons": [                   // faqat serial uchun, movie'da []
    {
      "id": 5, "number": 1, "title": null,
      "episodes": [
        { "id": 90, "number": 1, "title": null, "duration_sec": null,
          "is_available": true, "progress_sec": 0 }
      ]
    }
  ]
}
```

### `ContinueItem`
```json
{
  "title": { "...": "TitleCard" },
  "episode_id": 90,              // ?
  "episode_label": "1-fasl, 3-qism", // ?
  "position_sec": 1200,
  "duration_sec": 2700,
  "updated_at": "2026-09-28T10:00:00Z"
}
```

### `Genre`
```json
{ "slug": "jangari", "name": "Jangari", "count": 120 }
```

## Katalog

### `GET /v1/home`
```json
{
  "sections": [
    { "id": "hero",     "title": "Tavsiya",            "style": "hero",     "items": [TitleCard] },
    { "id": "continue", "title": "Davom ettirish",     "style": "continue", "items": [],
      "continue_items": [ContinueItem] },
    { "id": "new",      "title": "Yangi qo'shilganlar", "style": "row",     "items": [TitleCard] },
    { "id": "popular",  "title": "Ko'p ko'rilganlar",  "style": "row",      "items": [TitleCard] },
    { "id": "serials",  "title": "Seriallar",          "style": "row",      "items": [TitleCard] },
    { "id": "genre:jangari", "title": "Jangari",       "style": "row",      "items": [TitleCard] }
  ]
}
```
`style`: `hero` | `row` | `continue`. `continue_items` faqat `continue` bo'limida
bo'ladi (boshqalarida maydon yo'q). Bo'sh bo'lim qaytarilmaydi.

### `GET /v1/titles`
Query: `kind` (`movie`|`serial`, ixtiyoriy), `genre` (slug), `sort`
(`new` — default | `popular` | `year`), `cursor` (ixtiyoriy), `limit` (1–50, default 24).
```json
{ "items": [TitleCard], "next_cursor": "eyJvIjoyNH0" }   // next_cursor ? — oxirida null
```

### `GET /v1/titles/{id}` → `TitleDetail`

### `GET /v1/genres` → `{ "items": [Genre] }`

### `GET /v1/search?q=...&limit=20`
Kirill/lotin farqsiz (`Бойчечак` = `boychechak`). Raqam yuborilsa kod bo'yicha ham
qidiradi. `q` bo'sh bo'lsa 422.
```json
{ "items": [TitleCard] }
```

## Ijro (playback)

### `POST /v1/playback`
```json
// so'rov
{ "title_id": 17, "episode_id": null }   // serial uchun episode_id majburiy
// javob 200
{
  "stream_url": "https://api.kinomakoni.uz/v1/stream/<token>/video.mp4",
  "expires_at": "2026-09-28T16:00:00Z",
  "resume_position_sec": 1200
}
```
Xatolar: `premium_required` (403, `PREMIUM_ENFORCED=true` va kino premium bo'lsa),
`unavailable` (409, manba yo'q), `not_found` (404).

### `GET|HEAD /v1/stream/{token}/{filename}`
Autentifikatsiyasiz, imzolangan `token` bilan. HTTP `Range` to'liq qo'llanadi:
`206 Partial Content`, `Accept-Ranges: bytes`, `Content-Range`, `Content-Length`,
`Content-Type` (Telegram'dagi mime, odatda `video/mp4`). `Range` bo'lmasa `200`.
Muddati o'tgan / soxta token → 403. AVPlayer to'g'ridan-to'g'ri shu URL'ni o'ynaydi.

### `GET /v1/thumb/{token}/poster.jpg`
Imzolangan (muddatsiz) token bilan Telegram video thumbnail'ini qaytaradi
(`image/jpeg`, `Cache-Control: public, max-age=604800`). TMDB posteri yo'q
kinolar uchun `poster_url`/`backdrop_url` shu URL bo'ladi.

## Foydalanuvchi

| Metod | Yo'l | Tana | Javob |
|---|---|---|---|
| GET | `/v1/me` | — | `{ "id": 42, "created_at": "..." }` |
| GET | `/v1/me/favorites` | — | `{ "items": [TitleCard] }` (oxirgi qo'shilgan birinchi) |
| PUT | `/v1/me/favorites/{title_id}` | — | `204` (idempotent) |
| DELETE | `/v1/me/favorites/{title_id}` | — | `204` (idempotent) |
| GET | `/v1/me/continue` | — | `{ "items": [ContinueItem] }` (max 20, tugallanmaganlar) |
| PUT | `/v1/me/progress` | `{ "title_id": 17, "episode_id": null, "position_sec": 1200, "duration_sec": 10860 }` | `204` |

`position_sec >= 0.92 * duration_sec` bo'lsa ko'rish "tugallangan" hisoblanadi
va `continue` ro'yxatidan chiqadi. Ilova progressni har ~15 soniyada va
pleyer yopilganda yuboradi.

## Xizmat

- `GET /health` → `{ "status": "ok", "db": true, "telegram": true, "catalog_synced_at": "...?" }`

## Imzolangan token formati (backend ichki)

`app/core/signing.py`: `base64url(json) + "." + base64url(HMAC-SHA256)`.
Payload'lar:
- stream: `{"v":1,"src":"tg","ch":-1001234567890,"msg":555,"exp":1790000000}`
- thumb:  `{"v":1,"src":"tg-thumb","ch":-1001234567890,"msg":555}` (exp yo'q)

URL'larni faqat `app/core/media_urls.py` yasaydi; stream moduli faqat tekshiradi.
