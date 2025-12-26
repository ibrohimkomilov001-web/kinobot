import sqlite3
from config import DATABASE_NAME
from datetime import datetime, timedelta


def get_connection():
    """Database ga ulanish"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Jadvallarni yaratish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            full_name TEXT,
            username TEXT,
            is_premium INTEGER DEFAULT 0,
            referred_by INTEGER,
            joined_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Kinolar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            genre TEXT,
            duration TEXT,
            file_id TEXT NOT NULL,
            caption TEXT,
            added_by INTEGER,
            base_channel_id INTEGER,
            message_id INTEGER,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Kanallar jadvali (majburiy obuna)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER UNIQUE,
            channel_username TEXT,
            title TEXT,
            url TEXT,
            invite_link TEXT,
            is_request_group INTEGER DEFAULT 0,
            is_external_link INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # is_external_link ustunini qo'shish (eski bazalar uchun)
    try:
        cursor.execute('ALTER TABLE channels ADD COLUMN is_external_link INTEGER DEFAULT 0')
    except:
        pass
    
    # Bot sozlamalari jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Qo'shilish so'rovlari jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS join_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            request_date TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, channel_id)
        )
    ''')
    
    # Adminlar jadvali (kengaytirilgan huquqlar bilan)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            full_name TEXT,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP,
            can_movies INTEGER DEFAULT 1,
            can_channels INTEGER DEFAULT 1,
            can_broadcast INTEGER DEFAULT 1,
            can_stats INTEGER DEFAULT 1,
            can_premium INTEGER DEFAULT 1,
            can_admins INTEGER DEFAULT 0,
            can_settings INTEGER DEFAULT 0
        )
    ''')
    
    # Statistika jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            user_id INTEGER,
            watched_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Premium tariflar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS premium_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            price INTEGER NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Premium obunalar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS premium_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER,
            start_date TEXT DEFAULT CURRENT_TIMESTAMP,
            end_date TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (plan_id) REFERENCES premium_plans(id)
        )
    ''')
    
    # Premium to'lov so'rovlari jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS premium_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            file_id TEXT,
            file_type TEXT,
            status TEXT DEFAULT 'pending',
            admin_id INTEGER,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            processed_date TEXT,
            FOREIGN KEY (plan_id) REFERENCES premium_plans(id)
        )
    ''')
    
    # Default sozlamalar
    default_settings = [
        ('subscription_enabled', '1'),
        ('base_channel_id', ''),
        ('subscription_message', '❗️ Botdan foydalanish uchun quyidagi kanallarga obuna bo\'ling:'),
        ('channel_button_enabled', '1'),  # Kanal tugmasi yoniq/o'chiq
        ('channel_button_text', '📢 Kanal'),  # Tugma matni
        ('channel_button_url', ''),  # Tugma havolasi
    ]
    
    for key, value in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))
    
    # Admins jadvaliga yangi ustunlar qo'shish (migration)
    try:
        cursor.execute('ALTER TABLE admins ADD COLUMN can_movies INTEGER DEFAULT 1')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE admins ADD COLUMN can_channels INTEGER DEFAULT 1')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE admins ADD COLUMN can_broadcast INTEGER DEFAULT 1')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE admins ADD COLUMN can_stats INTEGER DEFAULT 1')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE admins ADD COLUMN can_premium INTEGER DEFAULT 1')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE admins ADD COLUMN can_admins INTEGER DEFAULT 0')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE admins ADD COLUMN can_settings INTEGER DEFAULT 0')
    except:
        pass
    
    # Referal tizimi uchun jadvallar
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referral_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL,
            bonus_amount INTEGER NOT NULL,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referrer_id) REFERENCES users(user_id),
            FOREIGN KEY (referred_id) REFERENCES users(user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawal_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            card_number TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            admin_id INTEGER,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            processed_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Users jadvaliga referral_balance ustunini qo'shish
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN referral_balance INTEGER DEFAULT 0')
    except:
        pass
    
    # Default referal sozlamalari
    referral_settings = [
        ('referral_enabled', '0'),
        ('referral_bonus', '500'),
        ('min_withdrawal', '10000'),
    ]
    
    for key, value in referral_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))
    
    conn.commit()
    conn.close()


# ===== FOYDALANUVCHILAR FUNKSIYALARI =====

def add_user(user_id: int, full_name: str, username: str = None):
    """Yangi foydalanuvchi qo'shish"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, full_name, username)
            VALUES (?, ?, ?)
        ''', (user_id, full_name, username))
        conn.commit()
    except Exception as e:
        print(f"Foydalanuvchi qo'shishda xatolik: {e}")
    finally:
        conn.close()


def get_users_count():
    """Foydalanuvchilar sonini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_all_users():
    """Barcha foydalanuvchilarni olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


# ===== KINOLAR FUNKSIYALARI =====

def add_movie(code: str, title: str, file_id: str, genre: str = None, duration: str = None,
              caption: str = None, added_by: int = None):
    """Yangi kino qo'shish"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO movies (code, title, genre, duration, file_id, caption, added_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (code, title, genre, duration, file_id, caption, added_by))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Code allaqachon mavjud
    except Exception as e:
        print(f"Kino qo'shishda xatolik: {e}")
        return False
    finally:
        conn.close()


def add_movie_with_message_id(code: str, title: str, file_id: str, genre: str = None, duration: str = None,
                               caption: str = None, added_by: int = None, 
                               base_channel_id: int = None, message_id: int = None):
    """Yangi kino qo'shish - baza kanal message_id bilan"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO movies (code, title, genre, duration, file_id, caption, added_by, base_channel_id, message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (code, title, genre, duration, file_id, caption, added_by, base_channel_id, message_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Code allaqachon mavjud
    except Exception as e:
        print(f"Kino qo'shishda xatolik: {e}")
        return False
    finally:
        conn.close()


def get_movie_by_code(code: str):
    """Kod bo'yicha kinoni topish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM movies WHERE code = ?', (code,))
    movie = cursor.fetchone()
    conn.close()
    return movie


def delete_movie(code: str):
    """Kinoni o'chirish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM movies WHERE code = ?', (code,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_movies_count():
    """Kinolar sonini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM movies')
    count = cursor.fetchone()[0]
    conn.close()
    return count


def search_movies(query: str):
    """Kinolarni qidirish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM movies 
        WHERE title LIKE ? OR code LIKE ?
        LIMIT 10
    ''', (f'%{query}%', f'%{query}%'))
    movies = cursor.fetchall()
    conn.close()
    return movies


def get_all_movies():
    """Barcha kinolarni olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM movies ORDER BY id DESC')
    movies = cursor.fetchall()
    conn.close()
    return movies


# ===== STATISTIKA =====

def add_view(movie_id: int, user_id: int):
    """Ko'rish statistikasini qo'shish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO statistics (movie_id, user_id)
        VALUES (?, ?)
    ''', (movie_id, user_id))
    conn.commit()
    conn.close()


def get_total_views():
    """Jami ko'rishlar soni"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM statistics')
    count = cursor.fetchone()[0]
    conn.close()
    return count


# ===== KANALLAR FUNKSIYALARI =====

def add_channel(channel_id: int, channel_username: str, title: str, url: str = None, 
                invite_link: str = None, is_request_group: bool = False, is_external_link: bool = False):
    """Yangi kanal qo'shish"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if not url and channel_username:
            url = f"https://t.me/{channel_username.replace('@', '')}"
        cursor.execute('''
            INSERT INTO channels (channel_id, channel_username, title, url, invite_link, is_request_group, is_external_link)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (channel_id, channel_username, title, url, invite_link, 1 if is_request_group else 0, 1 if is_external_link else 0))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Kanal qo'shishda xatolik: {e}")
        return False
    finally:
        conn.close()


def get_all_channels():
    """Barcha faol kanallarni olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM channels WHERE is_active = 1')
    rows = cursor.fetchall()
    conn.close()
    # Row ni dict ga o'tkazish
    channels = []
    for row in rows:
        channels.append({
            'id': row['id'],
            'channel_id': row['channel_id'],
            'channel_username': row['channel_username'],
            'title': row['title'],
            'url': row['url'],
            'invite_link': row['invite_link'],
            'is_request_group': row['is_request_group'],
            'is_external_link': row['is_external_link'] if 'is_external_link' in row.keys() else 0,
            'is_active': row['is_active'],
            'added_date': row['added_date']
        })
    return channels


def get_channel_by_id(channel_id: int):
    """Kanal ID bo'yicha topish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM channels WHERE channel_id = ?', (channel_id,))
    channel = cursor.fetchone()
    conn.close()
    return channel


def delete_channel(channel_id: int):
    """Kanalni o'chirish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM channels WHERE channel_id = ?', (channel_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_channels_count():
    """Kanallar sonini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM channels WHERE is_active = 1')
    count = cursor.fetchone()[0]
    conn.close()
    return count


# ===== SOZLAMALAR FUNKSIYALARI =====

def get_setting(key: str, default: str = None):
    """Sozlamani olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default


def set_setting(key: str, value: str):
    """Sozlamani saqlash"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
    ''', (key, value))
    conn.commit()
    conn.close()


def is_subscription_enabled():
    """Majburiy obuna yoqilganmi"""
    return get_setting('subscription_enabled', '1') == '1'


def toggle_subscription():
    """Majburiy obunani yoqish/o'chirish"""
    current = is_subscription_enabled()
    set_setting('subscription_enabled', '0' if current else '1')
    return not current


def get_base_channel():
    """Baza kanalni olish"""
    return get_setting('base_channel_id', '')


def set_base_channel(channel_id: str):
    """Baza kanalni sozlash"""
    set_setting('base_channel_id', channel_id)


def get_subscription_message():
    """Obuna xabarini olish"""
    return get_setting('subscription_message', '❗️ Botdan foydalanish uchun quyidagi kanallarga obuna bo\'ling:')


def set_subscription_message(message: str):
    """Obuna xabarini o'zgartirish"""
    set_setting('subscription_message', message)


# ===== KANAL TUGMASI SOZLAMALARI =====

def is_channel_button_enabled():
    """Kanal tugmasi yoniqmi"""
    return get_setting('channel_button_enabled', '1') == '1'


def toggle_channel_button():
    """Kanal tugmasini yoniq/o'chiq qilish"""
    current = is_channel_button_enabled()
    set_setting('channel_button_enabled', '0' if current else '1')
    return not current


def get_channel_button_text():
    """Kanal tugmasi matnini olish"""
    return get_setting('channel_button_text', '📢 Kanal')


def set_channel_button_text(text: str):
    """Kanal tugmasi matnini o'zgartirish"""
    set_setting('channel_button_text', text)


def get_channel_button_url():
    """Kanal tugmasi havolasini olish"""
    return get_setting('channel_button_url', '')


def set_channel_button_url(url: str):
    """Kanal tugmasi havolasini o'zgartirish"""
    set_setting('channel_button_url', url)


# ===== ADMINLAR FUNKSIYALARI =====

def add_admin(user_id: int, full_name: str = None, permissions: dict = None):
    """Admin qo'shish"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Default huquqlar
    default_perms = {
        'can_movies': 1,
        'can_channels': 1,
        'can_broadcast': 1,
        'can_stats': 1,
        'can_premium': 1,
        'can_admins': 0,
        'can_settings': 0
    }
    
    if permissions:
        default_perms.update(permissions)
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO admins 
            (user_id, full_name, can_movies, can_channels, can_broadcast, can_stats, can_premium, can_admins, can_settings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, full_name,
            default_perms['can_movies'],
            default_perms['can_channels'],
            default_perms['can_broadcast'],
            default_perms['can_stats'],
            default_perms['can_premium'],
            default_perms['can_admins'],
            default_perms['can_settings']
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Admin qo'shishda xatolik: {e}")
        return False
    finally:
        conn.close()


def remove_admin(user_id: int):
    """Adminni o'chirish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_all_admins():
    """Barcha adminlarni olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM admins')
    admins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return admins


def get_admin_permissions(user_id: int):
    """Admin huquqlarini olish"""
    from config import ADMINS
    
    # Config admin - barcha huquqlar
    if user_id in ADMINS:
        return {
            'can_movies': True,
            'can_channels': True,
            'can_broadcast': True,
            'can_stats': True,
            'can_premium': True,
            'can_admins': True,
            'can_settings': True,
            'is_super': True
        }
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT can_movies, can_channels, can_broadcast, can_stats, can_premium, can_admins, can_settings
        FROM admins WHERE user_id = ?
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'can_movies': bool(row[0]),
            'can_channels': bool(row[1]),
            'can_broadcast': bool(row[2]),
            'can_stats': bool(row[3]),
            'can_premium': bool(row[4]),
            'can_admins': bool(row[5]),
            'can_settings': bool(row[6]),
            'is_super': False
        }
    return None


def update_admin_permission(user_id: int, permission: str, value: bool):
    """Admin huquqini yangilash"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'''
            UPDATE admins SET {permission} = ? WHERE user_id = ?
        ''', (1 if value else 0, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Huquq yangilashda xatolik: {e}")
        return False
    finally:
        conn.close()


def is_admin(user_id: int):
    """Foydalanuvchi adminmi tekshirish"""
    from config import ADMINS
    db_admins = get_all_admins()
    return user_id in ADMINS or user_id in db_admins


def has_permission(user_id: int, permission: str):
    """Admin ma'lum huquqga egami tekshirish"""
    perms = get_admin_permissions(user_id)
    if not perms:
        return False
    return perms.get(permission, False)


# ===== STATISTIKA KENGAYTIRILGAN =====

def get_today_users():
    """Bugun qo'shilgan foydalanuvchilar"""
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE DATE(joined_date) = ?
    ''', (today,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_today_views():
    """Bugungi ko'rishlar"""
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(*) FROM statistics 
        WHERE DATE(watched_date) = ?
    ''', (today,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_weekly_users():
    """Haftalik yangi foydalanuvchilar"""
    conn = get_connection()
    cursor = conn.cursor()
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE DATE(joined_date) >= ?
    ''', (week_ago,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


# ============ Qo'shilish so'rovlari ============

def add_join_request(user_id: int, channel_id: int):
    """Qo'shilish so'rovini saqlash"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO join_requests (user_id, channel_id, request_date)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, channel_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Join request saqlashda xatolik: {e}")
        return False
    finally:
        conn.close()


def has_join_request(user_id: int, channel_id: int) -> bool:
    """Foydalanuvchi so'rov yuborgan yoki yo'qligini tekshirish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM join_requests 
        WHERE user_id = ? AND channel_id = ?
    ''', (user_id, channel_id))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def remove_join_request(user_id: int, channel_id: int):
    """So'rovni o'chirish (qabul qilinganda yoki rad etilganda)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM join_requests WHERE user_id = ? AND channel_id = ?
    ''', (user_id, channel_id))
    conn.commit()
    conn.close()


# ============ Premium funksiyalari ============

def add_premium_plan(name: str, duration_days: int, price: int, description: str = None):
    """Yangi tarif qo'shish"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO premium_plans (name, duration_days, price, description)
            VALUES (?, ?, ?, ?)
        ''', (name, duration_days, price, description))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def get_all_premium_plans():
    """Barcha tariflarni olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM premium_plans WHERE is_active = 1')
    plans = cursor.fetchall()
    conn.close()
    return [dict(p) for p in plans]


def get_premium_plan(plan_id: int):
    """Tarif ma'lumotlarini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM premium_plans WHERE id = ?', (plan_id,))
    plan = cursor.fetchone()
    conn.close()
    return dict(plan) if plan else None


def delete_premium_plan(plan_id: int):
    """Tarifni o'chirish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE premium_plans SET is_active = 0 WHERE id = ?', (plan_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def add_premium_request(user_id: int, plan_id: int, file_id: str, file_type: str):
    """Premium so'rov qo'shish"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO premium_requests (user_id, plan_id, file_id, file_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, plan_id, file_id, file_type))
        conn.commit()
        return cursor.lastrowid
    except:
        return None
    finally:
        conn.close()


def get_pending_premium_requests():
    """Kutilayotgan so'rovlarni olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pr.*, pp.name as plan_name, pp.duration_days, pp.price,
               u.full_name, u.username
        FROM premium_requests pr
        JOIN premium_plans pp ON pr.plan_id = pp.id
        JOIN users u ON pr.user_id = u.user_id
        WHERE pr.status = 'pending'
        ORDER BY pr.created_date DESC
    ''')
    requests = cursor.fetchall()
    conn.close()
    return [dict(r) for r in requests]


def get_premium_request(request_id: int):
    """So'rov ma'lumotlarini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pr.*, pp.name as plan_name, pp.duration_days, pp.price
        FROM premium_requests pr
        JOIN premium_plans pp ON pr.plan_id = pp.id
        WHERE pr.id = ?
    ''', (request_id,))
    request = cursor.fetchone()
    conn.close()
    return dict(request) if request else None


def approve_premium_request(request_id: int, admin_id: int):
    """Premium so'rovni tasdiqlash"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # So'rov ma'lumotlarini olish
    cursor.execute('''
        SELECT pr.user_id, pp.duration_days 
        FROM premium_requests pr
        JOIN premium_plans pp ON pr.plan_id = pp.id
        WHERE pr.id = ?
    ''', (request_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False
    
    user_id = result['user_id']
    duration_days = result['duration_days']
    
    # Obunani qo'shish
    end_date = (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d %H:%M:%S')
    
    # Mavjud obunani tekshirish
    cursor.execute('SELECT * FROM premium_subscriptions WHERE user_id = ? AND is_active = 1', (user_id,))
    existing = cursor.fetchone()
    
    if existing:
        # Mavjud obunaga qo'shish
        current_end = datetime.strptime(existing['end_date'], '%Y-%m-%d %H:%M:%S')
        new_end = current_end + timedelta(days=duration_days)
        cursor.execute('UPDATE premium_subscriptions SET end_date = ? WHERE id = ?', 
                      (new_end.strftime('%Y-%m-%d %H:%M:%S'), existing['id']))
    else:
        # Yangi obuna
        cursor.execute('''
            INSERT INTO premium_subscriptions (user_id, plan_id, end_date)
            VALUES (?, (SELECT plan_id FROM premium_requests WHERE id = ?), ?)
        ''', (user_id, request_id, end_date))
    
    # So'rovni yangilash
    cursor.execute('''
        UPDATE premium_requests 
        SET status = 'approved', admin_id = ?, processed_date = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (admin_id, request_id))
    
    conn.commit()
    conn.close()
    return True


def reject_premium_request(request_id: int, admin_id: int):
    """Premium so'rovni rad etish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE premium_requests 
        SET status = 'rejected', admin_id = ?, processed_date = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (admin_id, request_id))
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def is_premium_user(user_id: int) -> bool:
    """Foydalanuvchi premium ekanligini tekshirish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM premium_subscriptions 
        WHERE user_id = ? AND is_active = 1 AND end_date > CURRENT_TIMESTAMP
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def get_user_premium_info(user_id: int):
    """Foydalanuvchi premium ma'lumotlarini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ps.*, pp.name as plan_name
        FROM premium_subscriptions ps
        LEFT JOIN premium_plans pp ON ps.plan_id = pp.id
        WHERE ps.user_id = ? AND ps.is_active = 1 AND ps.end_date > CURRENT_TIMESTAMP
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None


def get_premium_users_count():
    """Premium foydalanuvchilar soni"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM premium_subscriptions 
        WHERE is_active = 1 AND end_date > CURRENT_TIMESTAMP
    ''')
    count = cursor.fetchone()[0]
    conn.close()
    return count


def is_premium_enabled() -> bool:
    """Premium tizimi yoniqligini tekshirish"""
    return get_setting('premium_enabled') == '1'


def set_premium_enabled(enabled: bool):
    """Premium tizimini yoqish/o'chirish"""
    set_setting('premium_enabled', '1' if enabled else '0')


def get_payment_card():
    """To'lov kartasini olish"""
    return get_setting('payment_card')


def set_payment_card(card: str):
    """To'lov kartasini saqlash"""
    set_setting('payment_card', card)


# ============ Kengaytirilgan Statistika ============

def get_daily_stats(days: int = 7):
    """Kunlik statistika"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # Yangi foydalanuvchilar
        cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(joined_date) = ?', (date,))
        new_users = cursor.fetchone()[0]
        
        # Ko'rishlar
        cursor.execute('SELECT COUNT(*) FROM statistics WHERE DATE(watched_date) = ?', (date,))
        views = cursor.fetchone()[0]
        
        stats.append({
            'date': date,
            'new_users': new_users,
            'views': views
        })
    
    conn.close()
    return stats


def get_top_movies(limit: int = 10):
    """Eng ko'p ko'rilgan kinolar"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.code, m.title, COUNT(s.id) as views
        FROM movies m
        LEFT JOIN statistics s ON m.id = s.movie_id
        GROUP BY m.id
        ORDER BY views DESC
        LIMIT ?
    ''', (limit,))
    movies = cursor.fetchall()
    conn.close()
    return [dict(m) for m in movies]


def get_active_users(days: int = 7):
    """Faol foydalanuvchilar (oxirgi X kunda kino ko'rganlar)"""
    conn = get_connection()
    cursor = conn.cursor()
    date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM statistics 
        WHERE DATE(watched_date) >= ?
    ''', (date,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_monthly_stats():
    """Oylik statistika"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = []
    for i in range(12):
        date = datetime.now() - timedelta(days=i*30)
        month_start = date.replace(day=1).strftime('%Y-%m-%d')
        if i == 0:
            month_end = datetime.now().strftime('%Y-%m-%d')
        else:
            month_end = (date.replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT COUNT(*) FROM users 
            WHERE DATE(joined_date) >= ? AND DATE(joined_date) < ?
        ''', (month_start, month_end))
        new_users = cursor.fetchone()[0]
        
        stats.append({
            'month': date.strftime('%Y-%m'),
            'new_users': new_users
        })
    
    conn.close()
    return stats[::-1]


# ===== REFERAL TIZIMI FUNKSIYALARI =====

def is_referral_enabled():
    """Referal tizimi yoniqmi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'referral_enabled'")
    result = cursor.fetchone()
    conn.close()
    return result[0] == '1' if result else False


def set_referral_enabled(enabled: bool):
    """Referal tizimini yoniq/o'chiq qilish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES ('referral_enabled', ?)
    ''', ('1' if enabled else '0',))
    conn.commit()
    conn.close()


def get_referral_bonus():
    """Har bir referal uchun bonus summasi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'referral_bonus'")
    result = cursor.fetchone()
    conn.close()
    return int(result[0]) if result else 500


def set_referral_bonus(amount: int):
    """Referal bonus summasini belgilash"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES ('referral_bonus', ?)
    ''', (str(amount),))
    conn.commit()
    conn.close()


def get_min_withdrawal():
    """Minimal pul chiqarish summasi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'min_withdrawal'")
    result = cursor.fetchone()
    conn.close()
    return int(result[0]) if result else 10000


def set_min_withdrawal(amount: int):
    """Minimal pul chiqarish summasini belgilash"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES ('min_withdrawal', ?)
    ''', (str(amount),))
    conn.commit()
    conn.close()


def add_user_with_referral(user_id: int, full_name: str, username: str = None, referred_by: int = None):
    """Yangi foydalanuvchi qo'shish (referal bilan)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Foydalanuvchi mavjudligini tekshirish
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Foydalanuvchi mavjud, ma'lumotlarni yangilash
            cursor.execute('''
                UPDATE users SET full_name = ?, username = ? WHERE user_id = ?
            ''', (full_name, username, user_id))
            conn.commit()
            conn.close()
            return False  # Yangi emas
        
        # Yangi foydalanuvchi qo'shish
        cursor.execute('''
            INSERT INTO users (user_id, full_name, username, referred_by)
            VALUES (?, ?, ?, ?)
        ''', (user_id, full_name, username, referred_by))
        
        # Agar referal bo'lsa, taklif qilgan foydalanuvchiga bonus berish
        if referred_by:
            bonus = get_referral_bonus()
            cursor.execute('''
                UPDATE users SET referral_balance = COALESCE(referral_balance, 0) + ? 
                WHERE user_id = ?
            ''', (bonus, referred_by))
            
            # Referal tarixiga qo'shish
            cursor.execute('''
                INSERT INTO referral_history (referrer_id, referred_id, bonus_amount)
                VALUES (?, ?, ?)
            ''', (referred_by, user_id, bonus))
        
        conn.commit()
        conn.close()
        return True  # Yangi foydalanuvchi
    except Exception as e:
        print(f"Foydalanuvchi qo'shishda xatolik: {e}")
        conn.close()
        return False


def get_user_referral_balance(user_id: int):
    """Foydalanuvchining referal balansini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT referral_balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] else 0


def get_user_referral_count(user_id: int):
    """Foydalanuvchi taklif qilgan odamlar soni"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_user_referrals(user_id: int):
    """Foydalanuvchi taklif qilgan odamlar ro'yxati"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, full_name, username, joined_date 
        FROM users WHERE referred_by = ?
        ORDER BY joined_date DESC
    ''', (user_id,))
    referrals = cursor.fetchall()
    conn.close()
    return referrals


def get_referral_history(user_id: int):
    """Foydalanuvchi referal tarixi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT rh.*, u.full_name, u.username 
        FROM referral_history rh
        LEFT JOIN users u ON rh.referred_id = u.user_id
        WHERE rh.referrer_id = ?
        ORDER BY rh.created_date DESC
    ''', (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history


def create_withdrawal_request(user_id: int, amount: int, card_number: str):
    """Pul chiqarish so'rovi yaratish"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Balansni tekshirish
        cursor.execute('SELECT referral_balance FROM users WHERE user_id = ?', (user_id,))
        balance = cursor.fetchone()
        if not balance or balance[0] < amount:
            conn.close()
            return False, "Balans yetarli emas"
        
        # So'rov yaratish
        cursor.execute('''
            INSERT INTO withdrawal_requests (user_id, amount, card_number, status)
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, amount, card_number))
        
        # Balansdan ayirish
        cursor.execute('''
            UPDATE users SET referral_balance = referral_balance - ? WHERE user_id = ?
        ''', (amount, user_id))
        
        conn.commit()
        conn.close()
        return True, "So'rov yuborildi"
    except Exception as e:
        conn.close()
        return False, str(e)


def get_pending_withdrawals():
    """Kutilayotgan pul chiqarish so'rovlari"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT w.*, u.full_name, u.username 
        FROM withdrawal_requests w
        LEFT JOIN users u ON w.user_id = u.user_id
        WHERE w.status = 'pending'
        ORDER BY w.created_date ASC
    ''')
    requests = cursor.fetchall()
    conn.close()
    return requests


def get_withdrawal_request(request_id: int):
    """Bitta pul chiqarish so'rovini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT w.*, u.full_name, u.username 
        FROM withdrawal_requests w
        LEFT JOIN users u ON w.user_id = u.user_id
        WHERE w.id = ?
    ''', (request_id,))
    request = cursor.fetchone()
    conn.close()
    return request


def approve_withdrawal(request_id: int, admin_id: int):
    """Pul chiqarish so'rovini tasdiqlash"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE withdrawal_requests 
            SET status = 'approved', admin_id = ?, processed_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (admin_id, request_id))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False


def reject_withdrawal(request_id: int, admin_id: int):
    """Pul chiqarish so'rovini rad etish"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # So'rov ma'lumotlarini olish
        cursor.execute('SELECT user_id, amount FROM withdrawal_requests WHERE id = ?', (request_id,))
        req = cursor.fetchone()
        if req:
            # Pulni qaytarish
            cursor.execute('''
                UPDATE users SET referral_balance = referral_balance + ? WHERE user_id = ?
            ''', (req[1], req[0]))
            
            # Statusni yangilash
            cursor.execute('''
                UPDATE withdrawal_requests 
                SET status = 'rejected', admin_id = ?, processed_date = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (admin_id, request_id))
            
            conn.commit()
            conn.close()
            return True
        conn.close()
        return False
    except:
        conn.close()
        return False


def get_total_referral_stats():
    """Umumiy referal statistikasi"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Jami referallar
    cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by IS NOT NULL')
    total_referrals = cursor.fetchone()[0]
    
    # Jami to'langan bonus
    cursor.execute('SELECT COALESCE(SUM(bonus_amount), 0) FROM referral_history')
    total_bonuses = cursor.fetchone()[0]
    
    # Jami chiqarilgan pul
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM withdrawal_requests WHERE status = 'approved'")
    total_withdrawn = cursor.fetchone()[0]
    
    # Kutilayotgan so'rovlar
    cursor.execute("SELECT COUNT(*) FROM withdrawal_requests WHERE status = 'pending'")
    pending_requests = cursor.fetchone()[0]
    
    # Top referralchilar
    cursor.execute('''
        SELECT u.user_id, u.full_name, u.username, COUNT(r.user_id) as ref_count
        FROM users u
        LEFT JOIN users r ON r.referred_by = u.user_id
        WHERE r.referred_by IS NOT NULL
        GROUP BY u.user_id
        ORDER BY ref_count DESC
        LIMIT 10
    ''')
    top_referrers = cursor.fetchall()
    
    conn.close()
    return {
        'total_referrals': total_referrals,
        'total_bonuses': total_bonuses,
        'total_withdrawn': total_withdrawn,
        'pending_requests': pending_requests,
        'top_referrers': top_referrers
    }


def get_user_withdrawal_history(user_id: int):
    """Foydalanuvchining pul chiqarish tarixi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM withdrawal_requests 
        WHERE user_id = ?
        ORDER BY created_date DESC
    ''', (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history


def get_referral_message():
    """Referal xabarini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'referral_message'")
    result = cursor.fetchone()
    conn.close()
    default_message = """🎬 Siz ham kino ko'ring va pul ishlang!

✅ Do'stlaringizni taklif qiling
💰 Har bir do'stingiz uchun bonus oling
💳 Pulni kartangizga chiqaring"""
    return result[0] if result else default_message


def set_referral_message(message: str):
    """Referal xabarini saqlash"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES ('referral_message', ?)
    ''', (message,))
    conn.commit()
    conn.close()


# ===== START XABARI SOZLAMALARI =====

def get_start_message():
    """Start xabarini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'start_message'")
    result = cursor.fetchone()
    conn.close()
    default_message = """🎬 <b>Kino Bot</b>ga xush kelibsiz!

📌 Kino kodini yuboring va kinoni oling!"""
    return result[0] if result else default_message


def set_start_message(message: str):
    """Start xabarini saqlash"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES ('start_message', ?)
    ''', (message,))
    conn.commit()
    conn.close()


def get_start_media():
    """Start media (rasm/gif) olish - {'type': 'photo'/'animation', 'file_id': '...'}"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'start_media_type'")
    media_type = cursor.fetchone()
    cursor.execute("SELECT value FROM settings WHERE key = 'start_media_file_id'")
    file_id = cursor.fetchone()
    conn.close()
    
    if media_type and file_id:
        return {'type': media_type[0], 'file_id': file_id[0]}
    return None


def set_start_media(media_type: str, file_id: str):
    """Start media saqlash"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES ('start_media_type', ?)
    ''', (media_type,))
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES ('start_media_file_id', ?)
    ''', (file_id,))
    conn.commit()
    conn.close()


def delete_start_media():
    """Start media o'chirish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM settings WHERE key = 'start_media_type'")
    cursor.execute("DELETE FROM settings WHERE key = 'start_media_file_id'")
    conn.commit()
    conn.close()


# ===== BOT UMUMIY SOZLAMALARI =====

def get_bot_name():
    """Bot nomini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'bot_name'")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Kino Bot"


def set_bot_name(name: str):
    """Bot nomini saqlash"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES ('bot_name', ?)
    ''', (name,))
    conn.commit()
    conn.close()


def is_bot_active():
    """Bot faolmi?"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'bot_active'")
    result = cursor.fetchone()
    conn.close()
    return result[0] == '1' if result else True


def set_bot_active(active: bool):
    """Botni yoqish/o'chirish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES ('bot_active', ?)
    ''', ('1' if active else '0',))
    conn.commit()
    conn.close()


def get_maintenance_message():
    """Texnik ishlar xabarini olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'maintenance_message'")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "🔧 Bot texnik ishlar sababli vaqtincha to'xtatilgan. Tez orada qaytamiz!"


def set_maintenance_message(message: str):
    """Texnik ishlar xabarini saqlash"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES ('maintenance_message', ?)
    ''', (message,))
    conn.commit()
    conn.close()


# ===== PROFESSIONAL DATA ANALYTICS =====

def get_hourly_stats(date: str = None):
    """Soatlik statistika - qaysi soatlarda foydalanuvchilar faol"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    hourly_data = {}
    for hour in range(24):
        hour_str = f"{hour:02d}"
        cursor.execute('''
            SELECT COUNT(*) FROM statistics 
            WHERE DATE(watched_date) = ? AND strftime('%H', watched_date) = ?
        ''', (date, hour_str))
        hourly_data[hour] = cursor.fetchone()[0]
    
    conn.close()
    return hourly_data


def get_peak_hours(days: int = 7):
    """Eng faol soatlarni aniqlash"""
    conn = get_connection()
    cursor = conn.cursor()
    
    date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT strftime('%H', watched_date) as hour, COUNT(*) as count
        FROM statistics
        WHERE DATE(watched_date) >= ?
        GROUP BY hour
        ORDER BY count DESC
        LIMIT 5
    ''', (date_from,))
    
    results = cursor.fetchall()
    conn.close()
    
    return [{'hour': int(r[0]), 'count': r[1]} for r in results]


def get_growth_rate(period_days: int = 30):
    """O'sish tezligini hisoblash (foizda)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Joriy davr
    current_start = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(*) FROM users WHERE DATE(joined_date) >= ?
    ''', (current_start,))
    current_users = cursor.fetchone()[0]
    
    # Oldingi davr
    prev_start = (datetime.now() - timedelta(days=period_days*2)).strftime('%Y-%m-%d')
    prev_end = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE DATE(joined_date) >= ? AND DATE(joined_date) < ?
    ''', (prev_start, prev_end))
    prev_users = cursor.fetchone()[0]
    
    conn.close()
    
    if prev_users == 0:
        return {'current': current_users, 'previous': prev_users, 'growth_rate': 100.0}
    
    growth_rate = ((current_users - prev_users) / prev_users) * 100
    return {
        'current': current_users,
        'previous': prev_users,
        'growth_rate': round(growth_rate, 2)
    }


def get_retention_rate(days: int = 7):
    """Qaytib kelish koeffitsienti - foydalanuvchilar necha marotaba qaytib keladi"""
    conn = get_connection()
    cursor = conn.cursor()
    
    date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Jami foydalanuvchilar
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # Oxirgi X kunda faol bo'lgan foydalanuvchilar
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM statistics 
        WHERE DATE(watched_date) >= ?
    ''', (date_from,))
    active_users = cursor.fetchone()[0]
    
    conn.close()
    
    if total_users == 0:
        return {'total': 0, 'active': 0, 'retention_rate': 0}
    
    retention = (active_users / total_users) * 100
    return {
        'total': total_users,
        'active': active_users,
        'retention_rate': round(retention, 2)
    }


def get_user_activity_distribution():
    """Foydalanuvchilar faollik bo'yicha taqsimoti"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Har bir foydalanuvchi nechta kino ko'rgan
    cursor.execute('''
        SELECT 
            CASE 
                WHEN view_count = 0 THEN 'passive'
                WHEN view_count BETWEEN 1 AND 5 THEN 'light'
                WHEN view_count BETWEEN 6 AND 20 THEN 'medium'
                WHEN view_count BETWEEN 21 AND 50 THEN 'active'
                ELSE 'super_active'
            END as category,
            COUNT(*) as user_count
        FROM (
            SELECT u.user_id, COALESCE(COUNT(s.id), 0) as view_count
            FROM users u
            LEFT JOIN statistics s ON u.user_id = s.user_id
            GROUP BY u.user_id
        )
        GROUP BY category
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    categories = {
        'passive': 0,      # 0 ko'rish
        'light': 0,        # 1-5 ko'rish
        'medium': 0,       # 6-20 ko'rish
        'active': 0,       # 21-50 ko'rish
        'super_active': 0  # 50+ ko'rish
    }
    
    for r in results:
        categories[r[0]] = r[1]
    
    return categories


def get_movie_genres_stats():
    """Kino janrlari bo'yicha statistika"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COALESCE(m.genre, 'Noma''lum') as genre,
            COUNT(DISTINCT m.id) as movie_count,
            COUNT(s.id) as view_count
        FROM movies m
        LEFT JOIN statistics s ON m.id = s.movie_id
        GROUP BY genre
        ORDER BY view_count DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{'genre': r[0], 'movies': r[1], 'views': r[2]} for r in results]


def get_conversion_funnel():
    """Konversiya voronkasi - qancha foydalanuvchi qaysi bosqichda"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Jami foydalanuvchilar
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # Kamida 1 ta kino ko'rganlar
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM statistics')
    viewed_users = cursor.fetchone()[0]
    
    # 5+ kino ko'rganlar
    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT user_id, COUNT(*) as cnt FROM statistics 
            GROUP BY user_id HAVING cnt >= 5
        )
    ''')
    engaged_users = cursor.fetchone()[0]
    
    # Premium foydalanuvchilar
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_premium = 1')
    premium_users = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_users': total_users,
        'viewed_users': viewed_users,
        'engaged_users': engaged_users,
        'premium_users': premium_users,
        'view_rate': round((viewed_users / max(total_users, 1)) * 100, 2),
        'engage_rate': round((engaged_users / max(viewed_users, 1)) * 100, 2),
        'premium_rate': round((premium_users / max(total_users, 1)) * 100, 2)
    }


def get_daily_active_users(days: int = 30):
    """DAU - Kunlik faol foydalanuvchilar (oxirgi X kun)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    dau_data = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM statistics 
            WHERE DATE(watched_date) = ?
        ''', (date,))
        dau = cursor.fetchone()[0]
        
        dau_data.append({
            'date': date,
            'dau': dau
        })
    
    conn.close()
    return dau_data


def get_user_lifetime_value():
    """Foydalanuvchilar qiymati - eng faol foydalanuvchilar"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            u.user_id,
            u.full_name,
            u.username,
            u.is_premium,
            COUNT(s.id) as total_views,
            MIN(s.watched_date) as first_view,
            MAX(s.watched_date) as last_view
        FROM users u
        LEFT JOIN statistics s ON u.user_id = s.user_id
        GROUP BY u.user_id
        ORDER BY total_views DESC
        LIMIT 15
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{
        'user_id': r[0],
        'full_name': r[1] or 'Noma\'lum',
        'username': r[2],
        'is_premium': bool(r[3]),
        'total_views': r[4],
        'first_view': r[5],
        'last_view': r[6]
    } for r in results]


def get_weekly_comparison():
    """Hafta kunlari bo'yicha taqqoslash"""
    conn = get_connection()
    cursor = conn.cursor()
    
    week_days = {
        '0': 'Yakshanba',
        '1': 'Dushanba',
        '2': 'Seshanba',
        '3': 'Chorshanba',
        '4': 'Payshanba',
        '5': 'Juma',
        '6': 'Shanba'
    }
    
    cursor.execute('''
        SELECT 
            strftime('%w', watched_date) as weekday,
            COUNT(*) as view_count
        FROM statistics
        WHERE DATE(watched_date) >= DATE('now', '-30 days')
        GROUP BY weekday
        ORDER BY view_count DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return [{'day': week_days.get(r[0], 'Noma\'lum'), 'views': r[1]} for r in results]


def get_new_vs_returning():
    """Yangi va qaytib kelgan foydalanuvchilar"""
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Yangi foydalanuvchilar (hafta ichida qo'shilgan va kino ko'rgan)
    cursor.execute('''
        SELECT COUNT(DISTINCT s.user_id)
        FROM statistics s
        INNER JOIN users u ON s.user_id = u.user_id
        WHERE DATE(s.watched_date) >= ? AND DATE(u.joined_date) >= ?
    ''', (week_ago, week_ago))
    new_active = cursor.fetchone()[0]
    
    # Qaytib kelgan (eski foydalanuvchilar, lekin hafta ichida faol)
    cursor.execute('''
        SELECT COUNT(DISTINCT s.user_id)
        FROM statistics s
        INNER JOIN users u ON s.user_id = u.user_id
        WHERE DATE(s.watched_date) >= ? AND DATE(u.joined_date) < ?
    ''', (week_ago, week_ago))
    returning_active = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'new_active': new_active,
        'returning_active': returning_active,
        'total_active': new_active + returning_active
    }


def get_avg_session_depth():
    """O'rtacha sessiya chuqurligi - har bir tashrif nechta kino ko'radi"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT AVG(daily_views) 
        FROM (
            SELECT user_id, DATE(watched_date) as day, COUNT(*) as daily_views
            FROM statistics
            WHERE DATE(watched_date) >= DATE('now', '-30 days')
            GROUP BY user_id, day
        )
    ''')
    
    result = cursor.fetchone()[0]
    conn.close()
    
    return round(result, 2) if result else 0


def get_trending_movies(days: int = 7, limit: int = 10):
    """Trend kinolar - so'nggi kunlarda eng ko'p ko'rilganlar"""
    conn = get_connection()
    cursor = conn.cursor()
    
    date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    cursor.execute('''
        SELECT 
            m.code,
            m.title,
            m.genre,
            COUNT(s.id) as recent_views,
            (SELECT COUNT(*) FROM statistics WHERE movie_id = m.id) as total_views
        FROM movies m
        INNER JOIN statistics s ON m.id = s.movie_id
        WHERE DATE(s.watched_date) >= ?
        GROUP BY m.id
        ORDER BY recent_views DESC
        LIMIT ?
    ''', (date_from, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [{
        'code': r[0],
        'title': r[1],
        'genre': r[2] or 'Noma\'lum',
        'recent_views': r[3],
        'total_views': r[4]
    } for r in results]


def get_overview_stats():
    """Umumiy statistika xulosasi"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Asosiy ko'rsatkichlar
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM movies')
    total_movies = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM statistics')
    total_views = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_premium = 1')
    premium_users = cursor.fetchone()[0]
    
    # Bugungi
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(joined_date) = ?', (today,))
    today_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM statistics WHERE DATE(watched_date) = ?', (today,))
    today_views = cursor.fetchone()[0]
    
    # Haftalik
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(joined_date) >= ?', (week_ago,))
    weekly_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM statistics WHERE DATE(watched_date) >= ?', (week_ago,))
    weekly_views = cursor.fetchone()[0]
    
    # O'rtacha ko'rishlar
    cursor.execute('''
        SELECT AVG(view_count) FROM (
            SELECT COUNT(*) as view_count FROM statistics GROUP BY user_id
        )
    ''')
    avg_views_per_user = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_users': total_users,
        'total_movies': total_movies,
        'total_views': total_views,
        'premium_users': premium_users,
        'today_users': today_users,
        'today_views': today_views,
        'weekly_users': weekly_users,
        'weekly_views': weekly_views,
        'avg_views_per_user': round(avg_views_per_user, 2),
        'views_per_movie': round(total_views / max(total_movies, 1), 2)
    }


# Jadvallarni yaratish
create_tables()
