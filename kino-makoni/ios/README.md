# Kino Makoni — iOS ilova

iPhone uchun kino va seriallar tomosha qilish ilovasi. SwiftUI, iOS 26 **Liquid Glass**
dizayni (qorong'i mavzu), backend — `kino-makoni/backend` (FastAPI). API shartnomasi:
[`../docs/API.md`](../docs/API.md).

- Minimal iOS: **26.0**, faqat iPhone
- Xcode: **26+** (iOS 26 SDK — Liquid Glass API'lari uchun shart)
- Tashqi bog'liqliklar yo'q (SPM paketlarisiz)
- Swift til rejimi: 5 (`SWIFT_STRICT_CONCURRENCY = minimal`)

## Loyihani generatsiya qilish

`.xcodeproj` git'da saqlanmaydi — u `project.yml` dan [XcodeGen](https://github.com/yonaskolb/XcodeGen)
orqali yaratiladi:

```bash
brew install xcodegen
cd kino-makoni/ios
xcodegen generate        # yoki shunchaki: xcodegen
open KinoMakoni.xcodeproj
```

`project.yml` o'zgarsa yoki yangi fayl qo'shilsa — `xcodegen` ni qayta ishga tushiring.
`KinoMakoni/Info.plist` ham shu buyruq bilan yaratiladi (qo'lda tahrirlamang —
`project.yml` dagi `info.properties` ni o'zgartiring).

| Qiymat | |
|---|---|
| Loyiha / target / scheme | `KinoMakoni` |
| Bundle ID | `uz.kinomakoni.app` |
| Ko'rinadigan nom | Kino Makoni |
| Versiya | 1.0.0 (1) |

## Simulyatorda ishga tushirish

1. Xcode'da `KinoMakoni` scheme'ini va iPhone simulyatorini (iOS 26) tanlang.
2. **⌘R**. Imzo (signing) simulyator uchun shart emas.

Buyruq qatoridan:

```bash
xcodebuild -project KinoMakoni.xcodeproj -scheme KinoMakoni \
  -destination 'platform=iOS Simulator,name=iPhone 17' build
```

## API manzili (`API_BASE_URL`)

Server manzili build sozlamasi `API_BASE_URL` orqali beriladi va Info.plist'ga
`KMApiBaseURL` kaliti sifatida yoziladi. Ilova uni ishga tushganda o'qiydi.

```bash
xcodebuild ... API_BASE_URL="https://api.kinomakoni.uz"
```

Xcode ichida: target → Build Settings → `API_BASE_URL` (User-Defined) qiymatini
o'zgartiring. Mahalliy server uchun `http://localhost:8000` ham ishlaydi
(`NSAllowsLocalNetworking` yoqilgan).

Birinchi so'rovda ilova `POST /v1/auth/device` orqali anonim "mehmon" token oladi
(`device_id` Keychain'da saqlanadi). Token eskirsa (401) avtomatik yangilanadi.

## Demo rejim

`API_BASE_URL` **bo'sh** bo'lsa (standart holat) ilova **demo rejimda** ishlaydi:

- ichki katalog: ~20 ta o'zbekcha kino va 3 ta serial (`MockCatalog.swift`);
- posterlar o'rniga gradient o'rinbosarlar (tarmoqdan rasm yuklanmaydi);
- video — Apple'ning ochiq test oqimi (HLS);
- sevimlilar va ko'rish progressi xotirada saqlanadi (ilova yopilsa tozalanadi);
- ba'zi kinolar Premium (qulf oynasini ko'rsatish uchun) va bittasi "Tez orada".

Profil sahifasida joriy rejim ko'rsatiladi: **Demo rejim** yoki **Server**.

## Tuzilma

```
KinoMakoni/
  App/            @main, RootView (TabView), AppState (umumiy holat, ijro oqimi)
  Core/
    Config/       AppConfig — KMApiBaseURL, versiya
    Models/       API.md obyektlari (Decodable, snake_case → camelCase)
    Networking/   KinoService protokoli, LiveKinoService, MockKinoService
    Auth/         Keychain, DeviceIdentity, TokenStore
    Navigation/   TitleRoute, CatalogQuery, umumiy navigationDestination
  DesignSystem/   Theme (ranglar), PosterView, GlassChip, FlowLayout, skelet, formatlash
  Features/       Home, Search, Library, Profile, Detail, Player
  Resources/      Assets.xcassets (AppIcon, Logo — branding; AccentColor, LaunchBackground)
```

Rang tokenlari bitta joyda: `DesignSystem/Theme.swift` (oltin urg'u `#E8C166`,
ko'mir-qora fon `#0B0B0F`).

## CI

- Codemagic: repo ildizidagi `codemagic.yaml` (imzosiz IPA).
- GitHub Actions: `.github/workflows/kino-makoni-ios.yml` (kompilyatsiya tekshiruvi).

Ikkalasi ham `xcodegen generate` → `xcodebuild archive ... API_BASE_URL=...` ketma-ketligidan foydalanadi.
