# Kino Makoni — iPhone'ga sideload qilish (Codemagic + Sideloadly)

Apple Developer dasturisiz ham (yoki bepul Apple ID bilan ham) ilovani
o'z iPhone'ingizga o'rnatish yo'li. Ilova imzosiz `.ipa` sifatida
build qilinadi (Codemagic yoki GitHub Actions), so'ng **Sideloadly**
kompyuterda uni imzolab qurilmaga o'rnatadi.

## 1. `.ipa`ni build qilish

### A. Codemagic (tavsiya etiladi)

1. https://codemagic.io → **Sign up / Log in** (GitHub akkaunt bilan
   kirish qulay).
2. **Add application** → `ibrohimkomilov001-web/kinobot` repo'sini tanlang.
3. Codemagic repo ildizidagi `codemagic.yaml`ni avtomatik topadi va
   "YAML aniqlangan" deb ko'rsatadi — shu tarzda davom eting (workflow
   tanlashning hojati yo'q, fayl ichida allaqachon bor).
4. Hech narsa sozlash shart emas: `API_BASE_URL` (`https://api.kinomakoni.uz`)
   `codemagic.yaml` ichida turibdi. Demo rejim kerak bo'lsa (backendsiz,
   namunaviy katalog) — faylda uni `""` qiling.
5. **Start new build** → branch: **`claude/eager-lovelace-0db0j8`** (yoki
   `main`, birlashtirilgach) → workflow: **`kino-makoni-ios-unsigned`** →
   Start build.
6. Build tugagach **Artifacts** bo'limidan `KinoMakoni.ipa`ni yuklab oling.

### B. GitHub Actions (muqobil — kod kompilyatsiya bo'lishini tekshirish uchun)

1. GitHub repo → **Actions** → **Kino Makoni iOS (unsigned build check)**.
2. **Run workflow** → xohlasangiz `api_base_url` inputini to'ldiring
   (bo'sh = demo rejim) → Run.
3. Build tugagach ochib, pastdagi **Artifacts** bo'limidan
   `KinoMakoni-unsigned-ipa`ni yuklab oling (14 kun saqlanadi).

> Ikkalasi ham bir xil imzosiz `.ipa` beradi — Codemagic asosiy, GitHub
> Actions esa qo'shimcha/zaxira tekshiruv.

## 2. Kerakli dasturlar (kompyuterda)

- **Sideloadly**: https://sideloadly.io (Windows/macOS).
- **Apple ID** (oddiy, bepul akkaunt yetarli — App Store Connect shart
  emas).
- iPhone USB kabel bilan ulangan (yoki Wi-Fi orqali, Sideloadly
  qo'llaydi).

## 3. O'rnatish (Sideloadly bilan)

1. iPhone'da **Developer Mode**ni yoqing (agar hali yoqmagan bo'lsangiz,
   avval sideload qilib ko'rish kerak — quyida "Developer Mode" bo'limiga
   qarang, chunki ba'zi iOS versiyalarida bu rejim birinchi
   sideload'dan KEYIN yoqiladi).
2. Sideloadly'ni oching, iPhone'ni tanlang.
3. `.ipa` faylni Sideloadly oynasiga tortib tashlang (drag & drop).
4. **Apple ID** maydoniga o'z Apple ID'ingizni kiriting → **Start**.
5. Parol so'ralsa kiriting (ba'zan ilova-maxsus parol — Apple ID
   sozlamalaridan yaratiladi).
6. Sideloadly ilovani imzolab, qurilmaga o'rnatadi.

### Developer Mode yoqish (iOS 26)

**Sozlamalar → Umumiy → VPN va Qurilma boshqaruvi** (yoki **Privacy &
Security → Developer Mode**, joylashuvi iOS versiyasiga qarab farq
qilishi mumkin) → **Developer Mode** ni yoqing → iPhone qayta ishga
tushadi → tasdiqlang.

### Profilga ishonish (Trust)

Ilovani birinchi ochganda "Untrusted Developer" xabari chiqadi:
**Sozlamalar → Umumiy → VPN va Qurilma boshqaruvi** → o'z Apple
ID'ingiz/profilingiz ostida → **Trust "<Apple ID>"** → Trust.

## 4. Muddat va qayta imzolash

| Apple ID turi | Ilova ishlash muddati | Qayta imzolash |
|---|---|---|
| Bepul (oddiy Apple ID) | **7 kun** | Har hafta Sideloadly bilan qayta o'rnatish kerak (o'sha `.ipa` fayl bilan, qayta build shart emas) |
| Pullik Apple Developer ($99/yil) | **1 yil** | Yiliga bir marta |

Bepul akkaunt bilan ishlatsangiz, Sideloadly'da **"AltStore-style"**
avtomatik qayta imzolash sozlamasi ham bor (kompyuter va iPhone bir xil
Wi-Fi'da bo'lganda) — bu haftalik qo'lda ishni kamaytiradi, lekin
kompyuter va Sideloadly ishga tushib turishi kerak.

## 5. Muammolarni bartaraf etish

| Muammo | Sabab / Yechim |
|---|---|
| "Unable to install" / imzolash xatosi | Apple ID parolini tekshiring; ilova-maxsus parol kerak bo'lishi mumkin (appleid.apple.com → Sign-In and Security → App-Specific Passwords) |
| "Max devices/apps limit reached" | Bepul Apple ID bir vaqtda faqat 3 ta ilovani sideload qila oladi — eski `.ipa`larni Sozlamalar → Umumiy → VPN va Qurilma boshqaruvi'dan o'chiring |
| Ilova ochilmaydi, "Untrusted Developer" | 3-bo'limdagi "Profilga ishonish" qadamini bajaring |
| 7 kundan keyin ilova ochilmay qoldi | Normal holat (bepul akkaunt) — Sideloadly bilan qayta o'rnating |
| Ilovada hech narsa yuklanmayapti (bo'sh ekran) | `API_BASE_URL` noto'g'ri yoki backend ishlamayapti — `kino-makoni/docs/DEPLOY.md` bilan tekshiring, yoki `API_BASE_URL`ni bo'sh qoldirib demo rejimda sinab ko'ring |
| Codemagic build'da "xcodegen: command not found" | Kamdan-kam holat — `brew install xcodegen` qadami muvaffaqiyatsiz bo'lgan, build loglarini tekshiring |
| Codemagic build'da Swift kompilyatsiya xatosi | Build loglarida `error:` qatorlarini qidiring; xuddi shu xatoni GitHub Actions workflow ham ko'rsatadi (tezroq tekshirish uchun) |
| iPhone Developer Mode ko'rinmayapti | Avval bitta sideload urinib ko'ring — ba'zi qurilmalarda shu sozlama shundan keyin paydo bo'ladi; keyin qayta o'rnating |

## 6. Muhim eslatma

`API_BASE_URL` build vaqtida ilova ichiga "quyiladi" (Info.plist orqali) —
u sozlangandan keyin backend manzilini o'zgartirish uchun **qayta build**
va qayta sideload kerak bo'ladi (ilova ichidan sozlash oynasi yo'q).
