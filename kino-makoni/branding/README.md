# Kino Makoni Branding

## Hozirgi Holat

Hozirda ishlatilayotgan icon va logo - bu o'rinbosardir (placeholder). Haqiqiy logotipni qo'shganizdan so'ng, avtomatik ravishda barcha iOS ikonlarini qayta yaratish mumkin.

## Haqiqiy Logotipni Qo'shish

1. Haqiqiy logotipingizni `kino-makoni/branding/logo.png` fayli sifatida saqlab qo'ying.
   - Tavsiya: PNG format, 1024x1024 px (yoki katta), shaffof fon yoki kvadrat fon.

2. Script-ni ishga tushiring:
   ```bash
   pip install pillow
   python3 kino-makoni/branding/generate_icons.py
   ```

3. Qayta yaratilgan fayllarni Git'ga commit qiling:
   - `ios/KinoMakoni/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png`
   - `ios/KinoMakoni/Resources/Assets.xcassets/Logo.imageset/` (hammasi)
   - `branding/preview.png` (yangilangan)

## Fayllar

- `generate_icons.py` - Ikonlarni yaratadigan Python skripti
- `logo.png` - Haqiqiy logotip (siz qo'shishingiz kerak)
- `logo-placeholder.png` - Shaffof o'rinbosar logo
- `preview.png` - Branding preview banner

## O'rinbosar Design

Qora cinematic temadir:
- Fon: #07070B (qora-qora)
- Indigo glow: #1B1640
- Amber: #FFB23F
- Orange: #FF5E3A

Dizayn: amber play-triangle + orange film-frame border, shaffof fonda.
