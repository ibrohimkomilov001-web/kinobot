# -*- coding: utf-8 -*-
"""
Backup (Zaxira) tizimi
- Ma'lumotlar bazasini zaxiralash
- Telegram kanalga yuborish
- Avtomatik zaxiralash
- Tiklash (restore) funksiyasi
"""

import os
import asyncio
import shutil
import json
from datetime import datetime
from aiogram import Bot
from config import BOT_TOKEN, ADMINS
import database as db

# Backup sozlamalari
BACKUP_FOLDER = "backups"
DATABASE_FILE = "kino_bot.db"
ADMIN_ID = ADMINS[0] if ADMINS else 0

def create_backup_folder():
    """Backup papkasini yaratish"""
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

def create_backup():
    """
    Ma'lumotlar bazasini zaxiralash
    Returns: backup fayl nomi
    """
    create_backup_folder()
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_FOLDER, backup_filename)
    
    # Database faylini nusxalash
    if os.path.exists(DATABASE_FILE):
        shutil.copy2(DATABASE_FILE, backup_path)
        return backup_path
    return None

def create_json_backup():
    """
    Ma'lumotlarni JSON formatda zaxiralash
    (Boshqa tizimga ko'chirish uchun qulay)
    """
    create_backup_folder()
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"backup_{timestamp}.json"
    backup_path = os.path.join(BACKUP_FOLDER, backup_filename)
    
    # Barcha ma'lumotlarni olish
    data = {
        "backup_date": timestamp,
        "users": get_all_users_data(),
        "movies": get_all_movies_data(),
        "channels": get_all_channels_data(),
        "statistics": get_statistics_data()
    }
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return backup_path

def get_all_users_data():
    """Barcha foydalanuvchilar ma'lumotlarini olish"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        columns = [description[0] for description in cursor.description]
        users = []
        for row in cursor.fetchall():
            users.append(dict(zip(columns, row)))
        conn.close()
        return users
    except Exception as e:
        print(f"Foydalanuvchilarni olishda xato: {e}")
        return []

def get_all_movies_data():
    """Barcha kinolar ma'lumotlarini olish"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM movies")
        columns = [description[0] for description in cursor.description]
        movies = []
        for row in cursor.fetchall():
            movies.append(dict(zip(columns, row)))
        conn.close()
        return movies
    except Exception as e:
        print(f"Kinolarni olishda xato: {e}")
        return []

def get_all_channels_data():
    """Barcha kanallar ma'lumotlarini olish"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM channels")
        columns = [description[0] for description in cursor.description]
        channels = []
        for row in cursor.fetchall():
            channels.append(dict(zip(columns, row)))
        conn.close()
        return channels
    except Exception as e:
        print(f"Kanallarni olishda xato: {e}")
        return []

def get_statistics_data():
    """Statistika ma'lumotlarini olish"""
    try:
        return {
            "total_users": db.get_users_count(),
            "total_movies": db.get_movies_count(),
            "backup_time": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Statistikani olishda xato: {e}")
        return {}

def get_backup_list():
    """Barcha backup fayllar ro'yxatini olish"""
    create_backup_folder()
    backups = []
    
    for filename in os.listdir(BACKUP_FOLDER):
        if filename.endswith('.db') or filename.endswith('.json'):
            filepath = os.path.join(BACKUP_FOLDER, filename)
            size = os.path.getsize(filepath)
            created = datetime.fromtimestamp(os.path.getctime(filepath))
            backups.append({
                "filename": filename,
                "path": filepath,
                "size": size,
                "size_mb": round(size / (1024 * 1024), 2),
                "created": created.strftime("%Y-%m-%d %H:%M:%S")
            })
    
    # Eng yangisidan boshlab tartiblash
    backups.sort(key=lambda x: x['created'], reverse=True)
    return backups

def restore_from_backup(backup_path: str):
    """
    Backupdan tiklash
    Args:
        backup_path: Backup fayl yo'li
    Returns:
        bool: Muvaffaqiyatli yoki yo'q
    """
    try:
        if not os.path.exists(backup_path):
            return False, "Backup fayl topilmadi"
        
        if backup_path.endswith('.db'):
            # Joriy bazani zaxiralash
            if os.path.exists(DATABASE_FILE):
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                shutil.copy2(DATABASE_FILE, f"backups/pre_restore_{timestamp}.db")
            
            # Backupdan tiklash
            shutil.copy2(backup_path, DATABASE_FILE)
            return True, "Ma'lumotlar muvaffaqiyatli tiklandi!"
        
        elif backup_path.endswith('.json'):
            return restore_from_json(backup_path)
        
        return False, "Noto'g'ri fayl formati"
    
    except Exception as e:
        return False, f"Tiklashda xato: {e}"

def restore_from_json(json_path: str):
    """JSON backupdan tiklash"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Foydalanuvchilarni tiklash
        users_restored = 0
        for user in data.get('users', []):
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, joined_date, last_active, is_banned, referrer_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.get('user_id'),
                    user.get('username'),
                    user.get('first_name'),
                    user.get('last_name'),
                    user.get('joined_date'),
                    user.get('last_active'),
                    user.get('is_banned', 0),
                    user.get('referrer_id')
                ))
                users_restored += 1
            except Exception as e:
                print(f"User tiklashda xato: {e}")
        
        # Kinolarni tiklash
        movies_restored = 0
        for movie in data.get('movies', []):
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO movies 
                    (code, file_id, caption, added_date, views, added_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    movie.get('code'),
                    movie.get('file_id'),
                    movie.get('caption'),
                    movie.get('added_date'),
                    movie.get('views', 0),
                    movie.get('added_by')
                ))
                movies_restored += 1
            except Exception as e:
                print(f"Movie tiklashda xato: {e}")
        
        # Kanallarni tiklash
        channels_restored = 0
        for channel in data.get('channels', []):
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO channels 
                    (channel_id, channel_name, channel_link, is_required)
                    VALUES (?, ?, ?, ?)
                """, (
                    channel.get('channel_id'),
                    channel.get('channel_name'),
                    channel.get('channel_link'),
                    channel.get('is_required', 1)
                ))
                channels_restored += 1
            except Exception as e:
                print(f"Channel tiklashda xato: {e}")
        
        conn.commit()
        conn.close()
        
        return True, f"✅ Tiklandi!\n👥 {users_restored} foydalanuvchi\n🎬 {movies_restored} kino\n📢 {channels_restored} kanal"
    
    except Exception as e:
        return False, f"JSON tiklashda xato: {e}"

def delete_old_backups(keep_count: int = 10):
    """Eski backuplarni o'chirish (oxirgi N tasini saqlash)"""
    backups = get_backup_list()
    
    if len(backups) > keep_count:
        for backup in backups[keep_count:]:
            try:
                os.remove(backup['path'])
            except Exception as e:
                print(f"Backupni o'chirishda xato: {e}")

def get_backup_stats():
    """Backup statistikasi"""
    backups = get_backup_list()
    total_size = sum(b['size'] for b in backups)
    
    return {
        "total_backups": len(backups),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "latest_backup": backups[0] if backups else None,
        "oldest_backup": backups[-1] if backups else None
    }

async def send_backup_to_telegram(bot: Bot = None):
    """
    Backup faylini Telegram orqali adminga yuborish
    """
    from aiogram.types import FSInputFile
    
    try:
        # Backup yaratish
        db_backup = create_backup()
        json_backup = create_json_backup()
        
        if not bot:
            from aiogram.client.default import DefaultBotProperties
            from aiogram.enums import ParseMode
            bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            should_close = True
        else:
            should_close = False
        
        # Statistika
        stats = get_backup_stats()
        users_count = db.get_users_count()
        movies_count = db.get_movies_count()
        
        caption = f"""🗄 Avtomatik Backup

📅 Sana: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
👥 Foydalanuvchilar: {users_count}
🎬 Kinolar: {movies_count}
📦 Jami backuplar: {stats['total_backups']}
💾 Umumiy hajm: {stats['total_size_mb']} MB

✅ Backup muvaffaqiyatli yaratildi!"""
        
        # DB faylini yuborish
        if db_backup and os.path.exists(db_backup):
            document = FSInputFile(db_backup)
            await bot.send_document(
                chat_id=ADMIN_ID,
                document=document,
                caption=caption
            )
        
        # JSON faylini yuborish
        if json_backup and os.path.exists(json_backup):
            document = FSInputFile(json_backup)
            await bot.send_document(
                chat_id=ADMIN_ID,
                document=document,
                caption="📋 JSON format backup (boshqa tizimga ko'chirish uchun)"
            )
        
        if should_close:
            await bot.session.close()
        
        # Eski backuplarni tozalash
        delete_old_backups(keep_count=10)
        
        return True
    
    except Exception as e:
        print(f"Backupni yuborishda xato: {e}")
        return False

async def scheduled_backup(interval_hours: int = 24):
    """
    Avtomatik backup (har X soatda)
    """
    while True:
        await asyncio.sleep(interval_hours * 3600)  # Soatni sekundga aylantirish
        await send_backup_to_telegram()
        print(f"✅ Avtomatik backup yaratildi: {datetime.now()}")

# CLI uchun
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create":
            path = create_backup()
            print(f"✅ Backup yaratildi: {path}")
        
        elif command == "json":
            path = create_json_backup()
            print(f"✅ JSON backup yaratildi: {path}")
        
        elif command == "list":
            backups = get_backup_list()
            print("\n📦 Backuplar ro'yxati:\n")
            for i, b in enumerate(backups, 1):
                print(f"{i}. {b['filename']} - {b['size_mb']} MB - {b['created']}")
        
        elif command == "restore" and len(sys.argv) > 2:
            backup_path = sys.argv[2]
            success, message = restore_from_backup(backup_path)
            print(message)
        
        elif command == "send":
            asyncio.run(send_backup_to_telegram())
            print("✅ Backup Telegramga yuborildi!")
        
        else:
            print("""
🗄 Backup tizimi

Buyruqlar:
  python backup.py create  - DB backup yaratish
  python backup.py json    - JSON backup yaratish
  python backup.py list    - Backuplar ro'yxati
  python backup.py restore <path> - Backupdan tiklash
  python backup.py send    - Telegramga yuborish
            """)
    else:
        # Default: backup yaratish
        path = create_backup()
        print(f"✅ Backup yaratildi: {path}")
