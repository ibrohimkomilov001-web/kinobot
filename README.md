# 🎬 Telegram Kino Bot

Bu Telegram bot orqali kinolarni saqlash va foydalanuvchilarga ulashish mumkin.

## 📋 Xususiyatlari

- ✅ Kino qo'shish (faqat adminlar)
- ✅ Kino o'chirish (faqat adminlar)
- ✅ Kod yoki nom bo'yicha qidirish
- ✅ Deep link orqali kino ulashish
- ✅ Statistika ko'rish
- ✅ Barcha foydalanuvchilarga reklama yuborish
- ✅ Foydalanuvchilar bazasi

## 🚀 O'rnatish

### 1. Kerakli kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

### 2. Bot yaratish

1. Telegram'da [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomini va username ni kiriting
4. Bot tokenini oling

### 3. Sozlamalar

`config.py` faylini oching va quyidagilarni o'zgartiring:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # BotFather dan olingan token
ADMINS = [123456789]  # O'zingizning Telegram ID raqamingiz
```

**Telegram ID ni bilish uchun:** [@userinfobot](https://t.me/userinfobot) ga yozing

### 4. Botni ishga tushirish

```bash
python bot.py
```

## 📖 Foydalanish

### Admin buyruqlari

| Tugma | Vazifasi |
|-----------------
| ➕ Kino qo'shish | Yangi kino qo'shish |
| 🗑 Kino o'chirish | Kinoni o'chirish |
| 📢 Reklama | Barcha foydalanuvchilarga xabar yuborish |
| 👥 Foydalanuvchilar | Statistika ko'rish |

### Kino qo'shish tartibi

1. "➕ Kino qo'shish" tugmasini bosing
2. Kino kodini kiriting (masalan: 123)
3. Kino nomini kiriting
4. Video faylni yuboring

### Foydalanuvchi uchun

- Kino kodini yuboring → kino olinadi
- Kino nomini yozing → qidiruv natijalari

### Deep Link

Kino qo'shgandan so'ng bot sizga havola beradi:

https://t.me/YOUR_BOT?start=123
Bu havolani ulashsangiz, foydalanuvchi to'g'ridan-to'g'ri kinoni oladi.

## 📁 Fayl strukturasi

kino_bot/
├── bot.py              # Asosiy fayl
├── config.py           # Sozlamalar
├── database.py         # Database funksiyalari
├── keyboards.py        # Klaviaturalar
├── states.py           # FSM holatlari
├── requirements.txt    # Kutubxonalar
├── README.md           # Qo'llanma
└── handlers/
    ├── __init__.py
    ├── user_handlers.py    # Foydalanuvchi handlerlari
    ├── admin_handlers.py   # Admin handlerlari
    └── movie_handlers.py   # Kino qidirish handlerlari

## ⚠️ Muhim

- Bot tokenini hech kim bilan ulashmang
- Admin ID ni to'g'ri kiriting
- Video fayllar 50MB dan oshmasligi kerak (Telegram cheklovi)

## 📞 Yordam

Savollar bo'lsa, murojaat qiling.

---
Made with ❤️ in Uzbekistan
