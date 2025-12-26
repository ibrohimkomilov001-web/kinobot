import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("bot_token")

# Admin ID
ADMINS = [int(os.getenv("admin_id", "0"))]

# Database fayl nomi
DATABASE_NAME = "kino_bot.db"

# Kanal (ixtiyoriy) - foydalanuvchilar a'zo bo'lishi kerak bo'lgan kanal
CHANNEL_USERNAME = None  # Masalan: "@your_channel"
CHANNEL_ID = None  # Masalan: -1001234567890
