import asyncio
import logging
import sys
from datetime import datetime, time

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, ADMINS
from handlers import user_router, admin_router, movie_router
import backup
import cloud_backup
from database import create_tables


async def scheduled_backup(bot: Bot):
    """Har kuni soat 03:00 da avtomatik zaxira"""
    while True:
        now = datetime.now()
        # Keyingi 03:00 gacha kutish
        target = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if now.hour >= 3:
            # Agar 03:00 dan o'tgan bo'lsa, ertangi kunga
            target = target.replace(day=now.day + 1)
        
        wait_seconds = (target - now).total_seconds()
        logging.info(f"Keyingi avtomatik zaxira: {target.strftime('%Y-%m-%d %H:%M')}")
        
        await asyncio.sleep(wait_seconds)
        
        # Zaxira yaratish va yuborish
        try:
            await backup.send_backup_to_telegram(bot)
            await cloud_backup.upload_backup_to_cloud(bot)
            logging.info("✅ Avtomatik zaxira yaratildi va yuborildi!")
        except Exception as e:
            logging.error(f"❌ Avtomatik zaxira xatosi: {e}")


async def cloud_backup_periodic(bot: Bot):
    """Har 6 soatda cloud backup"""
    while True:
        await asyncio.sleep(6 * 3600)  # 6 soat
        try:
            await cloud_backup.upload_backup_to_cloud(bot)
            logging.info("☁️ Cloud backup yuklandi")
        except Exception as e:
            logging.error(f"Cloud backup xatosi: {e}")


async def main():
    """Asosiy funksiya"""
    
    # Logging sozlamalari
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    # Bot va Dispatcher yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # ⚡ MUHIM: Server qayta ishga tushganda clouddan tiklash
    logging.info("🔄 Database tekshirilmoqda...")
    await cloud_backup.auto_restore_on_startup(bot)
    
    # Database jadvallarini yaratish
    create_tables()
    logging.info("✅ Database tayyor")
    
    # Routerlarni qo'shish
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(movie_router)
    
    # Avtomatik zaxira vazifalarini ishga tushirish
    asyncio.create_task(scheduled_backup(bot))
    asyncio.create_task(cloud_backup_periodic(bot))
    
    # Botni ishga tushirish
    logging.info("Bot ishga tushdi!")
    logging.info("🗄 Avtomatik zaxira tizimi faol (har kuni soat 03:00)")
    logging.info("☁️ Cloud backup faol (har 6 soatda)")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
