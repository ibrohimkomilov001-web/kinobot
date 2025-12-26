# -*- coding: utf-8 -*-
"""
Cloud Backup Tizimi
- Telegram kanalga backup yuklash
- Botni ishga tushirganda avtomatik tiklash
- Railway/Heroku kabi serverlarda database saqlanib qoladi
"""

import os
import asyncio
import logging
from datetime import datetime
from aiogram import Bot
from aiogram.types import FSInputFile
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, ADMINS

DATABASE_FILE = "kino_bot.db"
BACKUP_CHANNEL_ID = None  # Admin ID ishlatiladi

def get_admin_id():
    """Admin ID olish"""
    return ADMINS[0] if ADMINS else None


async def upload_backup_to_cloud(bot: Bot = None):
    """
    Database faylini Telegramga yuklash
    File_id qaytaradi - keyinroq tiklash uchun
    """
    close_bot = False
    if not bot:
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        close_bot = True
    
    try:
        admin_id = get_admin_id()
        if not admin_id:
            logging.error("Admin ID topilmadi!")
            return None
        
        if not os.path.exists(DATABASE_FILE):
            logging.warning("Database fayli topilmadi!")
            return None
        
        # Database hajmini tekshirish
        file_size = os.path.getsize(DATABASE_FILE)
        if file_size == 0:
            logging.warning("Database bo'sh!")
            return None
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        caption = f"""☁️ Cloud Backup

📅 {timestamp}
💾 {round(file_size / 1024, 2)} KB

#cloud_backup #database"""
        
        document = FSInputFile(DATABASE_FILE)
        message = await bot.send_document(
            chat_id=admin_id,
            document=document,
            caption=caption
        )
        
        file_id = message.document.file_id
        
        # File ID ni saqlash
        save_last_backup_id(file_id)
        
        logging.info(f"☁️ Cloud backup yuklandi: {file_id[:20]}...")
        
        if close_bot:
            await bot.session.close()
        
        return file_id
    
    except Exception as e:
        logging.error(f"Cloud backup xatosi: {e}")
        if close_bot:
            await bot.session.close()
        return None


def save_last_backup_id(file_id: str):
    """Oxirgi backup file_id ni saqlash"""
    try:
        with open("last_backup_id.txt", "w") as f:
            f.write(file_id)
    except Exception as e:
        logging.error(f"File ID saqlashda xato: {e}")


def get_last_backup_id():
    """Oxirgi backup file_id ni olish"""
    try:
        if os.path.exists("last_backup_id.txt"):
            with open("last_backup_id.txt", "r") as f:
                return f.read().strip()
    except Exception as e:
        logging.error(f"File ID o'qishda xato: {e}")
    return None


async def restore_from_cloud(bot: Bot = None, file_id: str = None):
    """
    Telegramdan backup faylini yuklab olish va tiklash
    """
    close_bot = False
    if not bot:
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        close_bot = True
    
    try:
        # Agar file_id berilmagan bo'lsa, oxirgisini olish
        if not file_id:
            file_id = get_last_backup_id()
        
        if not file_id:
            logging.warning("Backup file_id topilmadi!")
            if close_bot:
                await bot.session.close()
            return False
        
        # Faylni yuklab olish
        file = await bot.get_file(file_id)
        
        # Faylni saqlash
        await bot.download_file(file.file_path, DATABASE_FILE)
        
        logging.info("☁️ Database clouddan tiklandi!")
        
        if close_bot:
            await bot.session.close()
        
        return True
    
    except Exception as e:
        logging.error(f"Cloud restore xatosi: {e}")
        if close_bot:
            await bot.session.close()
        return False


async def auto_restore_on_startup(bot: Bot):
    """
    Bot ishga tushganda avtomatik tiklash
    Agar database bo'sh yoki yo'q bo'lsa - clouddan tiklaydi
    """
    try:
        # Database mavjudligini tekshirish
        if os.path.exists(DATABASE_FILE):
            file_size = os.path.getsize(DATABASE_FILE)
            if file_size > 1024:  # 1KB dan katta bo'lsa - database mavjud
                logging.info("✅ Database mavjud, tiklash shart emas")
                return True
        
        # Database yo'q yoki bo'sh - clouddan tiklash
        logging.info("⚠️ Database topilmadi, clouddan tiklanmoqda...")
        
        file_id = get_last_backup_id()
        if file_id:
            success = await restore_from_cloud(bot, file_id)
            if success:
                logging.info("✅ Database clouddan muvaffaqiyatli tiklandi!")
                
                # Adminga xabar
                admin_id = get_admin_id()
                if admin_id:
                    try:
                        await bot.send_message(
                            admin_id,
                            "🔄 <b>Database avtomatik tiklandi!</b>\n\n"
                            "Server qayta ishga tushirilganda database clouddan tiklandi.",
                            parse_mode="HTML"
                        )
                    except:
                        pass
                
                return True
            else:
                logging.error("❌ Clouddan tiklashda xato!")
                return False
        else:
            logging.warning("⚠️ Cloud backup topilmadi, yangi database yaratiladi")
            return False
    
    except Exception as e:
        logging.error(f"Auto restore xatosi: {e}")
        return False


async def periodic_cloud_backup(bot: Bot, interval_hours: int = 6):
    """
    Har X soatda avtomatik cloud backup
    """
    while True:
        await asyncio.sleep(interval_hours * 3600)
        try:
            await upload_backup_to_cloud(bot)
            logging.info(f"☁️ Periodic cloud backup bajarildi")
        except Exception as e:
            logging.error(f"Periodic backup xatosi: {e}")


# Test uchun
if __name__ == "__main__":
    async def test():
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        
        # Backup yuklash
        file_id = await upload_backup_to_cloud(bot)
        print(f"Backup yuklandi: {file_id}")
        
        await bot.session.close()
    
    asyncio.run(test())
