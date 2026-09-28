# Brending — logo va ikonkalar

- `logo.png` — **asl logo** (foydalanuvchi bergan, 512×512): tilla kino lentasi + play belgisi.
- `generate_icons.py` — shu logodan barcha iOS assetlarini yaratadi:
  - `ios/.../AppIcon.appiconset/AppIcon-1024.png` — ilova ikonkasi (1024×1024, shaffofliksiz)
  - `ios/.../Logo.imageset/` — ilova ichidagi **shaffof** belgi (`Image("Logo")`), 1x/2x/3x
  - `preview.png` — 1200×630 banner
- `logo-placeholder.png` — logo bo'lmaganda ishlatiladigan zaxira belgi.

## Logoni yangilash

```bash
pip install pillow
# yangi logoni kino-makoni/branding/logo.png ga qo'ying (ideal: 1024×1024 PNG)
python3 kino-makoni/branding/generate_icons.py
```

Logo to'liq kvadrat ikonka (o'z qorong'i foni bilan) deb qabul qilinadi. Shaffof
belgi yorqinlik bo'yicha ajratiladi: tilla qismlar qoladi, qorong'i fon o'chadi.
Hozirgi logo 512×512 — 1024 ga kattalashtirilgan; asl 1024 PNG bo'lsa tiniqroq chiqadi.
