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
    
    # Premium yoqilgan va foydalanuvchi hali premium emas bo'lsa
    if premium_enabled and not is_premium:
        buttons.append([KeyboardButton(text="рџ’Ћ Premium obuna olish")])
    
    # Hech narsa yo'q bo'lsa - ReplyKeyboardRemove qaytarish
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
            [KeyboardButton(text="рџ“Љ Statistika"), KeyboardButton(text="рџ“є Kanal boshqaruvi")],
            [KeyboardButton(text="рџЋ¬ Kino boshqaruvi"), KeyboardButton(text="рџ“ў Xabar yuborish")],
            [KeyboardButton(text="рџ’Ћ Premium obuna"), KeyboardButton(text="рџ‘‘ Admin boshqaruvi")],
            [KeyboardButton(text="рџ”— Referal boshqaruvi")],
            [KeyboardButton(text="вљ™пёЏ Bot sozlamlari")],
        ],
        resize_keyboard=True
    )
    return keyboard


def admin_panel_keyboard():
    """Admin panel - Inline keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="рџ“Љ Statistika", callback_data="admin_stats"),
                InlineKeyboardButton(text="рџ“є Kanal boshqaruvi", callback_data="admin_channels")
            ],
            [
                InlineKeyboardButton(text="рџЋ¬ Kino boshqaruvi", callback_data="admin_movies"),
                InlineKeyboardButton(text="рџ“ў Xabar yuborish", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="рџ’Ћ Premium obuna", callback_data="admin_premium"),
                InlineKeyboardButton(text="рџ‘‘ Admin boshqaruvi", callback_data="admin_admins")
            ],
            [
                InlineKeyboardButton(text="рџ”— Referal boshqaruvi", callback_data="admin_referral")
            ],
            [
                InlineKeyboardButton(text="вљ™пёЏ Bot sozlamlari", callback_data="admin_settings")
            ]
        ]
    )
    return keyboard


def movie_management_keyboard(movies_count: int = 0, base_channel: str = None):
    """Kino boshqaruvi paneli"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="рџ“‹ Kinolar ro'yxati", callback_data="movies_list"),
                InlineKeyboardButton(text="вћ• Kino qo'shish", callback_data="movie_add")
            ],
            [
                InlineKeyboardButton(text="рџ—‘ Kino o'chirish", callback_data="movie_delete"),
                InlineKeyboardButton(text="рџ”Ќ Kino qidirish", callback_data="movie_search")
            ],
            [
                InlineKeyboardButton(text="рџ” Kanal tugmasi", callback_data="movie_channel_button")
            ],
            [
                InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="back_to_admin")
            ]
        ]
    )
    return keyboard


def channel_management_keyboard(subscription_enabled: bool = True, channels_count: int = 0):
    """Kanal boshqaruvi paneli"""
    toggle_text = "вќЊ Obunani o'chirish" if subscription_enabled else "вњ… Obunani yoqish"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=toggle_text, callback_data="channel_toggle_sub"),
                InlineKeyboardButton(text="рџ“‹ Kanallar ro'yxati", callback_data="channels_list")
            ],
            [
                InlineKeyboardButton(text="вћ• Kanal qo'shish", callback_data="channel_add"),
                InlineKeyboardButton(text="рџ”— Havola qo'shish", callback_data="channel_add_link")
            ],
            [
                InlineKeyboardButton(text="рџ‘Ґ Sorovli guruh", callback_data="channel_request_group"),
                InlineKeyboardButton(text="рџ—‘ O'chirish", callback_data="channel_delete")
            ],
            [
                InlineKeyboardButton(text=" Orqaga", callback_data="back_to_admin")
            ]
        ]
    )
    return keyboard


def select_base_channel_keyboard():
    """Baza kanal tanlash uchun keyboard (Telegram kanal tanlash oynasi)"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="рџ“Ѓ Baza kanal tanlash",
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
            [KeyboardButton(text="рџ”™ Orqaga qaytish")]
        ],
        resize_keyboard=True
    )
    return keyboard


def bot_settings_keyboard():
    """Bot sozlamalari - Reply keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="рџ“ќ Start xabarini tahrirlash")],
            [
                KeyboardButton(
                    text="рџ“Ѓ Baza kanal tanlash",
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
            [KeyboardButton(text="рџ”™ Orqaga qaytish")]
        ],
        resize_keyboard=True
    )
    return keyboard


def bot_settings_inline_keyboard():
    """Bot sozlamalari - Inline keyboard (callback uchun)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="рџ“ќ Start xabarini tahrirlash", callback_data="edit_start_message")],
            [InlineKeyboardButton(text="рџ“Ѓ Baza kanalni sozlash", callback_data="settings_base_channel")],
            [InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def start_message_keyboard(has_media: bool = False):
    """Start xabari sozlamalari"""
    buttons = [
        [InlineKeyboardButton(text="рџ“ќ Matnni tahrirlash", callback_data="edit_start_text")],
        [InlineKeyboardButton(text="рџ–ј Rasm qo'shish/o'zgartirish", callback_data="edit_start_photo")],
        [InlineKeyboardButton(text="рџЋ¬ GIF qo'shish/o'zgartirish", callback_data="edit_start_gif")],
    ]
    
    if has_media:
        buttons.append([InlineKeyboardButton(text="рџ—‘ Mediani o'chirish", callback_data="delete_start_media")])
    
    buttons.append([InlineKeyboardButton(text="рџ‘Ѓ Ko'rish", callback_data="preview_start_message")])
    buttons.append([InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="admin_bot_settings")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channel_button_settings_keyboard(is_enabled: bool):
    """Kanal tugmasi sozlamalari"""
    toggle_text = "рџ”ґ O'chirish" if is_enabled else "рџџў Yoqish"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=toggle_text, callback_data="channel_btn_toggle")
            ],
            [
                InlineKeyboardButton(text="вњЏпёЏ Matnni tahrirlash", callback_data="channel_btn_edit_text"),
                InlineKeyboardButton(text="рџ”— Linkni tahrirlash", callback_data="channel_btn_edit_url")
            ],
            [
                InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="movie_management")
            ]
        ]
    )
    return keyboard


def statistics_keyboard():
    """Professional statistika paneli"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="пїЅ Umumiy ko'rsatkichlar", callback_data="stats_overview")
            ],
            [
                InlineKeyboardButton(text="пїЅрџ‘Ґ Foydalanuvchilar", callback_data="stats_users"),
                InlineKeyboardButton(text="рџЋ¬ Kinolar", callback_data="stats_movies")
            ],
            [
                InlineKeyboardButton(text="рџ“€ O'sish tezligi", callback_data="stats_growth"),
                InlineKeyboardButton(text="рџ”„ Retention", callback_data="stats_retention")
            ],
            [
                InlineKeyboardButton(text="вЏ° Vaqt analitikasi", callback_data="stats_time"),
                InlineKeyboardButton(text="пїЅ Trendlar", callback_data="stats_trends")
            ],
            [
                InlineKeyboardButton(text="рџ“‰ Konversiya", callback_data="stats_funnel"),
                InlineKeyboardButton(text="рџ‘‘ Top userlar", callback_data="stats_top_users")
            ],
            [
                InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="back_to_admin")
            ]
        ]
    )
    return keyboard


def cancel_keyboard():
    """Bekor qilish tugmasi - Inline"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="вќЊ Bekor qilish", callback_data="cancel_action")]
        ]
    )
    return keyboard


def cancel_reply_keyboard():
    """Bekor qilish - Reply keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="вќЊ Bekor qilish")],
        ],
        resize_keyboard=True
    )
    return keyboard


def back_keyboard(callback_data: str = "back_to_admin"):
    """Orqaga qaytish"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="рџ”™ Orqaga", callback_data=callback_data)]
        ]
    )
    return keyboard


def movie_keyboard(movie_code: str):
    """Kino uchun inline tugmalar"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="рџ”— Do'stlarga ulashish", 
                                  switch_inline_query=f"kino_{movie_code}")]
        ]
    )
    return keyboard


def confirm_keyboard(action: str):
    """Tasdiqlash tugmalari"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="вњ… Ha", callback_data=f"confirm_{action}"),
                InlineKeyboardButton(text="вќЊ Yo'q", callback_data="cancel_action")
            ]
        ]
    )
    return keyboard


def subscription_keyboard(channels: list):
    """Obuna bo'lish uchun kanallar"""
    buttons = []
    for channel in channels:
        # So'rovli guruh uchun invite_link, oddiy kanal uchun url
        url = channel.get('invite_link') or channel.get('url') or f"https://t.me/{channel.get('channel_username', '')}"
        
        # Tugma nomi
        if channel.get('is_external_link'):
            # Tashqi havola uchun - nomi bilan
            btn_text = f"рџ”— {channel.get('title', 'Obuna')}"
        else:
            # Telegram kanal uchun - standart yozuv
            btn_text = "вћ• Kanalga obuna bo'lish"
        
        buttons.append([
            InlineKeyboardButton(text=btn_text, url=url)
        ])
    buttons.append([
        InlineKeyboardButton(text="вњ… Obunani tekshirish", callback_data="check_subscription")
    ])
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
                text=f"рџЋ¬ {movie['code']} - {movie['title'][:30]}",
                callback_data=f"view_movie_{movie['code']}"
            )
        ])
    
    # Pagination tugmalari
    nav_buttons = []
    total_pages = (len(movies) + per_page - 1) // per_page
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="в¬…пёЏ", callback_data=f"movies_page_{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current_page"))
    
    if end < len(movies):
        nav_buttons.append(InlineKeyboardButton(text="вћЎпёЏ", callback_data=f"movies_page_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="admin_movies")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def premium_management_keyboard(is_enabled: bool = False):
    """Premium boshqaruvi"""
    status = "рџџў Yoniq" if is_enabled else "рџ”ґ O'chiq"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"рџ“Љ Premium holati: {status}", callback_data="toggle_premium")],
            [
                InlineKeyboardButton(text="рџ“‹ Tariflar", callback_data="premium_plans"),
                InlineKeyboardButton(text="вћ• Tarif qo'shish", callback_data="add_premium_plan")
            ],
            [InlineKeyboardButton(text="рџ“Ё Kutilayotgan so'rovlar", callback_data="pending_premium_requests")],
            [InlineKeyboardButton(text="рџ’і To'lov kartasi", callback_data="set_payment_card")],
            [InlineKeyboardButton(text="рџ‘Ґ Premium foydalanuvchilar", callback_data="premium_users_list")],
            [InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def premium_plans_keyboard(plans: list):
    """Tariflar ro'yxati"""
    buttons = []
    for plan in plans:
        buttons.append([
            InlineKeyboardButton(
                text=f"рџ’Ћ {plan['name']} - {plan['price']:,} so'm",
                callback_data=f"view_plan_{plan['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="admin_premium")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def user_premium_plans_keyboard(plans: list):
    """Foydalanuvchi uchun tariflar"""
    buttons = []
    for plan in plans:
        buttons.append([
            InlineKeyboardButton(
                text=f"рџ’Ћ {plan['name']} - {plan['price']:,} so'm ({plan['duration_days']} kun)",
                callback_data=f"buy_plan_{plan['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="cancel_premium")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def premium_request_keyboard(request_id: int):
    """Premium so'rov uchun tugmalar"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="вњ… Tasdiqlash", callback_data=f"approve_premium_{request_id}"),
                InlineKeyboardButton(text="вќЊ Rad etish", callback_data=f"reject_premium_{request_id}")
            ]
        ]
    )
    return keyboard


# ===== XABAR YUBORISH (BROADCAST) =====

def broadcast_type_keyboard():
    """Xabar turini tanlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="рџ“ќ Oddiy matn", callback_data="broadcast_text")],
            [InlineKeyboardButton(text="рџ–ј Rasm + Matn", callback_data="broadcast_photo")],
            [InlineKeyboardButton(text="рџЋ¬ Video + Matn", callback_data="broadcast_video")],
            [InlineKeyboardButton(text="рџ“ќ Matn + Tugma", callback_data="broadcast_text_button")],
            [InlineKeyboardButton(text="рџ–ј Rasm + Matn + Tugma", callback_data="broadcast_photo_button")],
            [InlineKeyboardButton(text="рџЋ¬ Video + Matn + Tugma", callback_data="broadcast_video_button")],
            [InlineKeyboardButton(text="рџ“‹ Forward qilish", callback_data="broadcast_forward")],
            [InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def broadcast_confirm_keyboard():
    """Xabarni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="вњ… Yuborish", callback_data="broadcast_send"),
                InlineKeyboardButton(text="вќЊ Bekor qilish", callback_data="broadcast_cancel")
            ],
            [InlineKeyboardButton(text="вћ• Tugma qo'shish", callback_data="broadcast_add_button")]
        ]
    )
    return keyboard


def broadcast_button_keyboard():
    """Tugma qo'shish yoki davom etish"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="вћ• Yana tugma qo'shish", callback_data="broadcast_add_more_button")],
            [InlineKeyboardButton(text="вњ… Yuborish", callback_data="broadcast_send")],
            [InlineKeyboardButton(text="вќЊ Bekor qilish", callback_data="broadcast_cancel")]
        ]
    )
    return keyboard


def broadcast_skip_caption_keyboard():
    """Matn kiritmasdan o'tkazish"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="вЏ­ O'tkazish (matnsiz)", callback_data="broadcast_skip_caption")]
        ]
    )
    return keyboard


def cancel_broadcast_keyboard():
    """Bekor qilish tugmasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="вќЊ Bekor qilish")]
        ],
        resize_keyboard=True
    )
    return keyboard


# ===== ADMIN BOSHQARUVI =====

def admin_management_keyboard():
    """Admin boshqaruvi paneli"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="рџ“‹ Adminlar ro'yxati", callback_data="admins_list")],
            [
                InlineKeyboardButton(text="вћ• Admin qo'shish", callback_data="admin_add"),
                InlineKeyboardButton(text="рџ—‘ Admin o'chirish", callback_data="admin_remove")
            ],
            [InlineKeyboardButton(text="рџ”ђ Huquqlar", callback_data="admin_permissions")],
            [InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def admins_list_keyboard(admins: list, config_admins: list):
    """Adminlar ro'yxati tugmalari"""
    buttons = []
    for admin_id in admins:
        is_config = admin_id in config_admins
        status = "рџ‘‘" if is_config else "рџ‘¤"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {admin_id}",
                callback_data=f"view_admin_{admin_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="admin_admins")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_view_keyboard(admin_id: int, is_config_admin: bool):
    """Admin ma'lumotlari"""
    buttons = []
    if not is_config_admin:
        buttons.append([InlineKeyboardButton(text="пїЅ Huquqlarni boshqarish", callback_data=f"edit_perms_{admin_id}")])
        buttons.append([InlineKeyboardButton(text="пїЅрџ—‘ O'chirish", callback_data=f"confirm_remove_admin_{admin_id}")])
    buttons.append([InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="admins_list")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_remove_admin_keyboard(admin_id: int):
    """Adminni o'chirishni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="вњ… Ha, o'chirish", callback_data=f"remove_admin_{admin_id}"),
                InlineKeyboardButton(text="вќЊ Yo'q", callback_data="admins_list")
            ]
        ]
    )
    return keyboard


def admin_permissions_keyboard(admin_id: int, permissions: dict):
    """Admin huquqlarini boshqarish"""
    def perm_status(key):
        return "вњ…" if permissions.get(key) else "вќЊ"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{perm_status('can_movies')} Kino boshqaruvi",
                callback_data=f"toggle_perm_{admin_id}_can_movies"
            )],
            [InlineKeyboardButton(
                text=f"{perm_status('can_channels')} Kanal boshqaruvi",
                callback_data=f"toggle_perm_{admin_id}_can_channels"
            )],
            [InlineKeyboardButton(
                text=f"{perm_status('can_broadcast')} Xabar yuborish",
                callback_data=f"toggle_perm_{admin_id}_can_broadcast"
            )],
            [InlineKeyboardButton(
                text=f"{perm_status('can_stats')} Statistika",
                callback_data=f"toggle_perm_{admin_id}_can_stats"
            )],
            [InlineKeyboardButton(
                text=f"{perm_status('can_premium')} Premium boshqaruvi",
                callback_data=f"toggle_perm_{admin_id}_can_premium"
            )],
            [InlineKeyboardButton(
                text=f"{perm_status('can_admins')} Admin boshqaruvi",
                callback_data=f"toggle_perm_{admin_id}_can_admins"
            )],
            [InlineKeyboardButton(
                text=f"{perm_status('can_settings')} Bot sozlamalari",
                callback_data=f"toggle_perm_{admin_id}_can_settings"
            )],
            [InlineKeyboardButton(text="рџ”™ Orqaga", callback_data=f"view_admin_{admin_id}")]
        ]
    )
    return keyboard


def admin_menu_keyboard_dynamic(permissions: dict):
    """Admin menyu - huquqlarga ko'ra dinamik"""
    buttons = []
    
    if permissions.get('can_stats'):
        buttons.append(KeyboardButton(text="рџ“Љ Statistika"))
    if permissions.get('can_channels'):
        buttons.append(KeyboardButton(text="рџ“є Kanal boshqaruvi"))
    
    row1 = buttons[:2] if len(buttons) >= 2 else buttons
    buttons = buttons[2:]
    
    row2 = []
    if permissions.get('can_movies'):
        row2.append(KeyboardButton(text="рџЋ¬ Kino boshqaruvi"))
    if permissions.get('can_broadcast'):
        row2.append(KeyboardButton(text="рџ“ў Xabar yuborish"))
    
    row3 = []
    if permissions.get('can_premium'):
        row3.append(KeyboardButton(text="рџ’Ћ Premium obuna"))
    if permissions.get('can_admins'):
        row3.append(KeyboardButton(text="рџ‘‘ Admin boshqaruvi"))
    
    row4 = []
    if permissions.get('can_settings'):
        row4.append(KeyboardButton(text="вљ™пёЏ Bot sozlamlari"))
    
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
        keyboard_rows = [[KeyboardButton(text="рџ“Љ Statistika")]]
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard_rows,
        resize_keyboard=True
    )
    return keyboard


# ===== REFERAL TIZIMI KLAVIATURALARI =====

def referral_user_keyboard():
    """Foydalanuvchi referal menyusi - Reply keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="рџ”— Referal havolam")],
            [KeyboardButton(text="рџ’° Hisobim"), KeyboardButton(text="рџ’і Pul chiqarish")],
            [KeyboardButton(text="рџ“Љ Statistikam"), KeyboardButton(text="рџ“њ Tarix")],
            [KeyboardButton(text="рџ”™ Asosiy menyu")]
        ],
        resize_keyboard=True
    )
    return keyboard


def main_menu_with_referral_keyboard(is_premium: bool = False, premium_enabled: bool = False, referral_enabled: bool = False):
    """Asosiy menyu - referal bilan"""
    buttons = []
    
    # Premium yoqilgan va foydalanuvchi hali premium emas bo'lsa
    if premium_enabled and not is_premium:
        buttons.append([KeyboardButton(text="рџ’Ћ Premium obuna olish")])
    
    # Referal yoqilgan bo'lsa
    if referral_enabled:
        buttons.append([KeyboardButton(text="рџ’µ Referal - Pul ishlash")])
    
    # Hech narsa yo'q bo'lsa - ReplyKeyboardRemove qaytarish
    if not buttons:
        from aiogram.types import ReplyKeyboardRemove
        return ReplyKeyboardRemove()
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


def referral_admin_keyboard():
    """Admin referal boshqaruvi - Inline keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="рџ“Љ Referal statistika", callback_data="referral_stats")],
            [
                InlineKeyboardButton(text="вљ™пёЏ Sozlamalar", callback_data="referral_settings"),
                InlineKeyboardButton(text="рџ’і So'rovlar", callback_data="referral_requests")
            ],
            [InlineKeyboardButton(text="рџЏ† Top referralchilar", callback_data="referral_top")],
            [InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="back_to_admin")]
        ]
    )
    return keyboard


def referral_settings_keyboard(is_enabled: bool):
    """Referal sozlamalari"""
    toggle_text = "рџџў Yoniq - O'chirish uchun bosing" if is_enabled else "рџ”ґ O'chiq - Yoqish uchun bosing"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=toggle_text, callback_data="referral_toggle")],
            [InlineKeyboardButton(text="рџ’° Bonus summasini o'zgartirish", callback_data="referral_set_bonus")],
            [InlineKeyboardButton(text="рџ’і Min. chiqarish summasini o'zgartirish", callback_data="referral_set_min")],
            [InlineKeyboardButton(text="вњЏпёЏ Referal xabarini tahrirlash", callback_data="referral_edit_message")],
            [InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="admin_referral")]
        ]
    )
    return keyboard


def referral_link_keyboard(referral_link: str):
    """Referal havola tugmasi - yashil qo'shilish"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="рџџў Qo'shilish", url=referral_link)]
        ]
    )
    return keyboard


def withdrawal_requests_keyboard(requests: list):
    """Pul chiqarish so'rovlari ro'yxati"""
    buttons = []
    for req in requests[:20]:  # Max 20 ta
        user_name = req['full_name'] if req['full_name'] else f"ID: {req['user_id']}"
        amount = req['amount']
        buttons.append([
            InlineKeyboardButton(
                text=f"рџ’і {user_name} - {amount:,} so'm",
                callback_data=f"view_withdrawal_{req['id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="admin_referral")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def withdrawal_action_keyboard(request_id: int):
    """Pul chiqarish so'rovi uchun amallar"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="вњ… Tasdiqlash", callback_data=f"approve_withdrawal_{request_id}"),
                InlineKeyboardButton(text="вќЊ Rad etish", callback_data=f"reject_withdrawal_{request_id}")
            ],
            [InlineKeyboardButton(text="рџ”™ Orqaga", callback_data="referral_requests")]
        ]
    )
    return keyboard


def withdrawal_confirm_keyboard():
    """Pul chiqarish tasdiqlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="вњ… Ha, chiqarish", callback_data="confirm_withdrawal"),
                InlineKeyboardButton(text="вќЊ Bekor qilish", callback_data="cancel_withdrawal")
            ]
        ]
    )
    return keyboard

