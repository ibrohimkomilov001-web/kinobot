from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButtonRequestChat
)


def main_menu_keyboard(is_premium: bool = False, premium_enabled: bool = False):
    """Asosiy menyu"""
    buttons = []
    
    if premium_enabled and not is_premium:
        buttons.append([KeyboardButton(text="💎 Premium obuna olish")])
    
    if not buttons:
        from aiogram.types import ReplyKeyboardRemove
        return ReplyKeyboardRemove()
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


def admin_menu_keyboard():
    """Admin asosiy menyu - Reply keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📺 Kanal boshqaruvi")],
            [KeyboardButton(text="🎬 Kino boshqaruvi"), KeyboardButton(text="📢 Xabar yuborish")],
            [KeyboardButton(text="💎 Premium obuna"), KeyboardButton(text="👑 Admin boshqaruvi")],
            [KeyboardButton(text="🔗 Referal boshqaruvi"), KeyboardButton(text="🗄 Zaxira nusxa")],
            [KeyboardButton(text="⚙️ Bot sozlamlari")],
        ],
        resize_keyboard=True
    )
    return keyboard


def admin_panel_keyboard():
    """Admin panel - Inline keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
                InlineKeyboardButton(text="📺 Kanal boshqaruvi", callback_data="admin_channels")
            ],
            [
                InlineKeyboardButton(text="🎬 Kino boshqaruvi", callback_data="admin_movies"),
                InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="💎 Premium obuna", callback_data="admin_premium"),
                InlineKeyboardButton(text="👑 Admin boshqaruvi", callback_data="admin_admins")
            ],
            [
                InlineKeyboardButton(text="🔗 Referal boshqaruvi", callback_data="admin_referral")
            ],
            [
                InlineKeyboardButton(text="⚙️ Bot sozlamlari", callback_data="admin_settings")
            ]
        ]
    )
    return keyboard


def movie_management_keyboard(movies_count: int = 0, base_channel: str = None):
    """Kino boshqaruvi paneli"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Kinolar ro'yxati", callback_data="movies_list"),
                InlineKeyboardButton(text="➕ Kino qo'shish", callback_data="movie_add")
            ],
            [
                InlineKeyboardButton(text="🗑 Kino o'chirish", callback_data="movie_delete"),
                InlineKeyboardButton(text="🔍 Kino qidirish", callback_data="movie_search")
            ],
            [
                InlineKeyboardButton(text="📢 Kanal tugmasi", callback_data="movie_channel_button")
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")
            ]
        ]
    )
    return keyboard


def channel_management_keyboard(subscription_enabled: bool = True, channels_count: int = 0):
    """Kanal boshqaruvi paneli"""
    toggle_text = "❌ Obunani o'chirish" if subscription_enabled else "✅ Obunani yoqish"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=toggle_text, callback_data="channel_toggle_sub"),
                InlineKeyboardButton(text="📋 Kanallar ro'yxati", callback_data="channels_list")
            ],
            [
                InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="channel_add"),
                InlineKeyboardButton(text="🔗 Havola qo'shish", callback_data="channel_add_link")
            ],
            [
                InlineKeyboardButton(text="👥 Sorovli guruh", callback_data="channel_request_group"),
                InlineKeyboardButton(text="🗑 O'chirish", callback_data="channel_delete")
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")
            ]
        ]
    )
    return keyboard


def select_base_channel_keyboard():
    """Baza kanal tanlash uchun keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📁 Baza kanal tanlash",
                    request_chat=KeyboardButtonRequestChat(
                        request_id=1,
                        chat_is_channel=True,
                        chat_is_created=False,
                        chat_has_username=False,
                        chat_is_forum=False,
                        bot_is_member=True,
                        bot_administrator_rights=None,
                        user_administrator_rights=None
                    )
                )
            ],
            [KeyboardButton(text="🔙 Orqaga qaytish")]
        ],
        resize_keyboard=True
    )
    return keyboard


def bot_settings_keyboard():
    """Bot sozlamalari - Reply keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Start xabarini tahrirlash")],
            [
                KeyboardButton(
                    text="📁 Baza kanal tanlash",
                    request_chat=KeyboardButtonRequestChat(
                        request_id=1,
                        chat_is_channel=True,
                        chat_is_created=False,
                        chat_has_username=False,
                        chat_is_forum=False,
                        bot_is_member=True,
                        bot_administrator_rights=None,
                        user_administrator_rights=None
                    )
                )
            ],
            [KeyboardButton(text="🔙 Orqaga qaytish")]
        ],
        resize_keyboard=True
    )
    return keyboard


def bot_settings_inline_keyboard():
    """Bot sozlamalari - Inline keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Start xabarini tahrirlash", callback_data="edit_start_message")],
            [InlineKeyboardButton(text="📁 Baza kanalni sozlash", callback_data="settings_base_channel")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def start_message_keyboard(has_media: bool = False):
    """Start xabari sozlamalari"""
    buttons = [
        [InlineKeyboardButton(text="📝 Matnni tahrirlash", callback_data="edit_start_text")],
        [InlineKeyboardButton(text="🖼 Rasm qo'shish/o'zgartirish", callback_data="edit_start_photo")],
        [InlineKeyboardButton(text="🎬 GIF qo'shish/o'zgartirish", callback_data="edit_start_gif")],
    ]
    if has_media:
        buttons.append([InlineKeyboardButton(text="🗑 Mediani o'chirish", callback_data="delete_start_media")])
    buttons.append([InlineKeyboardButton(text="👁 Ko'rish", callback_data="preview_start_message")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_bot_settings")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channel_button_settings_keyboard(is_enabled: bool):
    """Kanal tugmasi sozlamalari"""
    toggle_text = "🔴 O'chirish" if is_enabled else "🟢 Yoqish"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data="channel_btn_toggle")],
            [
                InlineKeyboardButton(text="✏️ Matnni tahrirlash", callback_data="channel_btn_edit_text"),
                InlineKeyboardButton(text="🔗 Linkni tahrirlash", callback_data="channel_btn_edit_url")
            ],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="movie_management")]
        ]
    )
    return keyboard


def statistics_keyboard():
    """Professional statistika paneli"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Umumiy ko'rsatkichlar", callback_data="stats_overview")],
            [
                InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="stats_users"),
                InlineKeyboardButton(text="🎬 Kinolar", callback_data="stats_movies")
            ],
            [
                InlineKeyboardButton(text="📈 O'sish tezligi", callback_data="stats_growth"),
                InlineKeyboardButton(text="🔄 Retention", callback_data="stats_retention")
            ],
            [
                InlineKeyboardButton(text="⏰ Vaqt analitikasi", callback_data="stats_time"),
                InlineKeyboardButton(text="🔥 Trendlar", callback_data="stats_trends")
            ],
            [
                InlineKeyboardButton(text="📉 Konversiya", callback_data="stats_funnel"),
                InlineKeyboardButton(text="👑 Top userlar", callback_data="stats_top_users")
            ],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def cancel_keyboard():
    """Bekor qilish tugmasi - Inline"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action")]
        ]
    )
    return keyboard


def cancel_reply_keyboard():
    """Bekor qilish - Reply keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
    return keyboard


def back_keyboard(callback_data: str = "back_to_admin"):
    """Orqaga qaytish"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data=callback_data)]]
    )
    return keyboard


def movie_keyboard(movie_code: str):
    """Kino uchun inline tugmalar"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Do'stlarga ulashish", switch_inline_query=f"kino_{movie_code}")]
        ]
    )
    return keyboard


def confirm_keyboard(action: str):
    """Tasdiqlash tugmalari"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data=f"confirm_{action}"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="cancel_action")
            ]
        ]
    )
    return keyboard


def subscription_keyboard(channels: list):
    """Obuna bo'lish uchun kanallar"""
    buttons = []
    for channel in channels:
        url = channel.get('invite_link') or channel.get('url') or f"https://t.me/{channel.get('channel_username', '')}"
        if channel.get('is_external_link'):
            btn_text = f"🔗 {channel.get('title', 'Obuna')}"
        else:
            btn_text = "➕ Kanalga obuna bo'lish"
        buttons.append([InlineKeyboardButton(text=btn_text, url=url)])
    buttons.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def movies_list_keyboard(movies: list, page: int = 1, per_page: int = 10):
    """Kinolar ro'yxati - pagination bilan"""
    buttons = []
    start = (page - 1) * per_page
    end = start + per_page
    page_movies = movies[start:end]
    
    for movie in page_movies:
        buttons.append([
            InlineKeyboardButton(
                text=f"🎬 {movie['code']} - {movie['title'][:30]}",
                callback_data=f"view_movie_{movie['code']}"
            )
        ])
    
    nav_buttons = []
    total_pages = (len(movies) + per_page - 1) // per_page
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"movies_page_{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current_page"))
    if end < len(movies):
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"movies_page_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_movies")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def premium_management_keyboard(is_enabled: bool = False):
    """Premium boshqaruvi"""
    status = "🟢 Yoniq" if is_enabled else "🔴 O'chiq"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📊 Premium holati: {status}", callback_data="toggle_premium")],
            [
                InlineKeyboardButton(text="📋 Tariflar", callback_data="premium_plans"),
                InlineKeyboardButton(text="➕ Tarif qo'shish", callback_data="add_premium_plan")
            ],
            [InlineKeyboardButton(text="📨 Kutilayotgan so'rovlar", callback_data="pending_premium_requests")],
            [InlineKeyboardButton(text="💳 To'lov kartasi", callback_data="set_payment_card")],
            [InlineKeyboardButton(text="👥 Premium foydalanuvchilar", callback_data="premium_users_list")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def premium_plans_keyboard(plans: list):
    """Tariflar ro'yxati"""
    buttons = []
    for plan in plans:
        buttons.append([
            InlineKeyboardButton(
                text=f"💎 {plan['name']} - {plan['price']:,} so'm",
                callback_data=f"view_plan_{plan['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_premium")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def user_premium_plans_keyboard(plans: list):
    """Foydalanuvchi uchun tariflar"""
    buttons = []
    for plan in plans:
        buttons.append([
            InlineKeyboardButton(
                text=f"💎 {plan['name']} - {plan['price']:,} so'm ({plan['duration_days']} kun)",
                callback_data=f"buy_plan_{plan['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="cancel_premium")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def premium_request_keyboard(request_id: int):
    """Premium so'rov uchun tugmalar"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_premium_{request_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_premium_{request_id}")
            ]
        ]
    )
    return keyboard


def broadcast_type_keyboard():
    """Xabar turini tanlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Oddiy matn", callback_data="broadcast_text")],
            [InlineKeyboardButton(text="🖼 Rasm + Matn", callback_data="broadcast_photo")],
            [InlineKeyboardButton(text="🎬 Video + Matn", callback_data="broadcast_video")],
            [InlineKeyboardButton(text="📝 Matn + Tugma", callback_data="broadcast_text_button")],
            [InlineKeyboardButton(text="🖼 Rasm + Matn + Tugma", callback_data="broadcast_photo_button")],
            [InlineKeyboardButton(text="🎬 Video + Matn + Tugma", callback_data="broadcast_video_button")],
            [InlineKeyboardButton(text="📋 Forward qilish", callback_data="broadcast_forward")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def broadcast_confirm_keyboard():
    """Xabarni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast_send"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast_cancel")
            ],
            [InlineKeyboardButton(text="➕ Tugma qo'shish", callback_data="broadcast_add_button")]
        ]
    )
    return keyboard


def broadcast_button_keyboard():
    """Tugma qo'shish yoki davom etish"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Yana tugma qo'shish", callback_data="broadcast_add_more_button")],
            [InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast_send")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast_cancel")]
        ]
    )
    return keyboard


def broadcast_skip_caption_keyboard():
    """Matn kiritmasdan o'tkazish"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭ O'tkazish (matnsiz)", callback_data="broadcast_skip_caption")]
        ]
    )
    return keyboard


def cancel_broadcast_keyboard():
    """Bekor qilish tugmasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )
    return keyboard


def admin_management_keyboard():
    """Admin boshqaruvi paneli"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Adminlar ro'yxati", callback_data="admins_list")],
            [
                InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin_add"),
                InlineKeyboardButton(text="🗑 Admin o'chirish", callback_data="admin_remove")
            ],
            [InlineKeyboardButton(text="🔐 Huquqlar", callback_data="admin_permissions")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def admins_list_keyboard(admins: list, config_admins: list):
    """Adminlar ro'yxati tugmalari"""
    buttons = []
    for admin_id in admins:
        is_config = admin_id in config_admins
        status = "👑" if is_config else "👤"
        buttons.append([
            InlineKeyboardButton(text=f"{status} {admin_id}", callback_data=f"view_admin_{admin_id}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_admins")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_view_keyboard(admin_id: int, is_config_admin: bool):
    """Admin ma'lumotlari"""
    buttons = []
    if not is_config_admin:
        buttons.append([InlineKeyboardButton(text="⚙️ Huquqlarni boshqarish", callback_data=f"edit_perms_{admin_id}")])
        buttons.append([InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"confirm_remove_admin_{admin_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admins_list")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_remove_admin_keyboard(admin_id: int):
    """Adminni o'chirishni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"remove_admin_{admin_id}"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="admins_list")
            ]
        ]
    )
    return keyboard


def admin_permissions_keyboard(admin_id: int, permissions: dict):
    """Admin huquqlarini boshqarish"""
    def perm_status(key):
        return "✅" if permissions.get(key) else "❌"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{perm_status('can_movies')} Kino boshqaruvi", callback_data=f"toggle_perm_{admin_id}_can_movies")],
            [InlineKeyboardButton(text=f"{perm_status('can_channels')} Kanal boshqaruvi", callback_data=f"toggle_perm_{admin_id}_can_channels")],
            [InlineKeyboardButton(text=f"{perm_status('can_broadcast')} Xabar yuborish", callback_data=f"toggle_perm_{admin_id}_can_broadcast")],
            [InlineKeyboardButton(text=f"{perm_status('can_stats')} Statistika", callback_data=f"toggle_perm_{admin_id}_can_stats")],
            [InlineKeyboardButton(text=f"{perm_status('can_premium')} Premium boshqaruvi", callback_data=f"toggle_perm_{admin_id}_can_premium")],
            [InlineKeyboardButton(text=f"{perm_status('can_admins')} Admin boshqaruvi", callback_data=f"toggle_perm_{admin_id}_can_admins")],
            [InlineKeyboardButton(text=f"{perm_status('can_settings')} Bot sozlamalari", callback_data=f"toggle_perm_{admin_id}_can_settings")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"view_admin_{admin_id}")]
        ]
    )
    return keyboard


def admin_menu_keyboard_dynamic(permissions: dict):
    """Admin menyu - huquqlarga ko'ra dinamik"""
    buttons = []
    if permissions.get('can_stats'):
        buttons.append(KeyboardButton(text="📊 Statistika"))
    if permissions.get('can_channels'):
        buttons.append(KeyboardButton(text="📺 Kanal boshqaruvi"))
    
    row1 = buttons[:2] if len(buttons) >= 2 else buttons
    buttons = buttons[2:]
    
    row2 = []
    if permissions.get('can_movies'):
        row2.append(KeyboardButton(text="🎬 Kino boshqaruvi"))
    if permissions.get('can_broadcast'):
        row2.append(KeyboardButton(text="📢 Xabar yuborish"))
    
    row3 = []
    if permissions.get('can_premium'):
        row3.append(KeyboardButton(text="💎 Premium obuna"))
    if permissions.get('can_admins'):
        row3.append(KeyboardButton(text="👑 Admin boshqaruvi"))
    
    row4 = []
    if permissions.get('can_settings'):
        row4.append(KeyboardButton(text="⚙️ Bot sozlamlari"))
    
    keyboard_rows = []
    if row1:
        keyboard_rows.append(row1)
    if row2:
        keyboard_rows.append(row2)
    if row3:
        keyboard_rows.append(row3)
    if row4:
        keyboard_rows.append(row4)
    
    if not keyboard_rows:
        keyboard_rows = [[KeyboardButton(text="📊 Statistika")]]
    
    keyboard = ReplyKeyboardMarkup(keyboard=keyboard_rows, resize_keyboard=True)
    return keyboard


def referral_user_keyboard():
    """Foydalanuvchi referal menyusi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔗 Referal havolam")],
            [KeyboardButton(text="💰 Hisobim"), KeyboardButton(text="💳 Pul chiqarish")],
            [KeyboardButton(text="📊 Statistikam"), KeyboardButton(text="📜 Tarix")],
            [KeyboardButton(text="🔙 Asosiy menyu")]
        ],
        resize_keyboard=True
    )
    return keyboard


def main_menu_with_referral_keyboard(is_premium: bool = False, premium_enabled: bool = False, referral_enabled: bool = False):
    """Asosiy menyu - referal bilan"""
    buttons = []
    if premium_enabled and not is_premium:
        buttons.append([KeyboardButton(text="💎 Premium obuna olish")])
    if referral_enabled:
        buttons.append([KeyboardButton(text="💵 Referal - Pul ishlash")])
    if not buttons:
        from aiogram.types import ReplyKeyboardRemove
        return ReplyKeyboardRemove()
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


def referral_admin_keyboard():
    """Admin referal boshqaruvi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Referal statistika", callback_data="referral_stats")],
            [
                InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="referral_settings"),
                InlineKeyboardButton(text="💳 So'rovlar", callback_data="referral_requests")
            ],
            [InlineKeyboardButton(text="🏆 Top referralchilar", callback_data="referral_top")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def referral_settings_keyboard(is_enabled: bool):
    """Referal sozlamalari"""
    toggle_text = "🟢 Yoniq - O'chirish uchun bosing" if is_enabled else "🔴 O'chiq - Yoqish uchun bosing"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data="referral_toggle")],
            [InlineKeyboardButton(text="💰 Bonus summasini o'zgartirish", callback_data="referral_set_bonus")],
            [InlineKeyboardButton(text="💳 Min. chiqarish summasini o'zgartirish", callback_data="referral_set_min")],
            [InlineKeyboardButton(text="✏️ Referal xabarini tahrirlash", callback_data="referral_edit_message")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_referral")]
        ]
    )
    return keyboard


def referral_link_keyboard(referral_link: str):
    """Referal havola tugmasi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🟢 Qo'shilish", url=referral_link)]]
    )
    return keyboard


def withdrawal_requests_keyboard(requests: list):
    """Pul chiqarish so'rovlari ro'yxati"""
    buttons = []
    for req in requests[:20]:
        user_name = req['full_name'] if req['full_name'] else f"ID: {req['user_id']}"
        amount = req['amount']
        buttons.append([
            InlineKeyboardButton(text=f"💳 {user_name} - {amount:,} so'm", callback_data=f"view_withdrawal_{req['id']}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_referral")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def withdrawal_action_keyboard(request_id: int):
    """Pul chiqarish so'rovi uchun amallar"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_withdrawal_{request_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_withdrawal_{request_id}")
            ],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="referral_requests")]
        ]
    )
    return keyboard


def withdrawal_confirm_keyboard():
    """Pul chiqarish tasdiqlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, chiqarish", callback_data="confirm_withdrawal"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_withdrawal")
            ]
        ]
    )
    return keyboard


def backup_keyboard():
    """Zaxira nusxa boshqaruvi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📤 Zaxira yaratish", callback_data="backup_create"),
                InlineKeyboardButton(text="📋 JSON zaxira", callback_data="backup_json")
            ],
            [
                InlineKeyboardButton(text="☁️ Cloud backup", callback_data="backup_cloud"),
                InlineKeyboardButton(text="🔄 Clouddan tiklash", callback_data="backup_cloud_restore")
            ],
            [
                InlineKeyboardButton(text="📁 Zaxiralar ro'yxati", callback_data="backup_list"),
                InlineKeyboardButton(text="📊 Zaxira statistikasi", callback_data="backup_stats")
            ],
            [
                InlineKeyboardButton(text="📥 Tiklash (Restore)", callback_data="backup_restore")
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin")
            ]
        ]
    )
    return keyboard


def backup_list_keyboard(backups: list):
    """Zaxiralar ro'yxati"""
    buttons = []
    for i, backup in enumerate(backups[:10]):  # Oxirgi 10 ta
        filename = backup['filename'][:20] + "..." if len(backup['filename']) > 20 else backup['filename']
        buttons.append([
            InlineKeyboardButton(
                text=f"📦 {filename} ({backup['size_mb']} MB)", 
                callback_data=f"backup_select_{i}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_backup")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def backup_action_keyboard(backup_index: int):
    """Tanlangan zaxira uchun amallar"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📤 Telegramga yuborish", callback_data=f"backup_send_{backup_index}"),
                InlineKeyboardButton(text="♻️ Tiklash", callback_data=f"backup_do_restore_{backup_index}")
            ],
            [
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"backup_delete_{backup_index}")
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="backup_list")
            ]
        ]
    )
    return keyboard
