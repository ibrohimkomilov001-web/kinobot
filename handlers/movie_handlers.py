from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import (
    get_movie_by_code, search_movies, add_view, is_admin, get_base_channel,
    is_channel_button_enabled, get_channel_button_text, get_channel_button_url,
    is_subscription_enabled, get_all_channels, has_join_request, is_premium_user,
    is_premium_enabled
)
from keyboards import main_menu_keyboard, admin_menu_keyboard, movie_keyboard, subscription_keyboard
from states import SearchMovie

router = Router()


def get_user_keyboard(user_id: int):
    """Foydalanuvchi uchun klaviatura"""
    if is_admin(user_id):
        return admin_menu_keyboard()
    is_premium = is_premium_user(user_id)
    premium_enabled = is_premium_enabled()
    return main_menu_keyboard(is_premium, premium_enabled)


async def check_subscription(user_id: int, bot) -> bool:
    """Foydalanuvchi kanallarga obuna bo'lganligini tekshirish"""
    # Premium foydalanuvchilar uchun tekshirish shart emas
    if is_premium_user(user_id):
        return True
    
    if not is_subscription_enabled():
        return True
    
    channels = get_all_channels()
    if not channels:
        return True
    
    for channel in channels:
        channel_id = channel['channel_id']
        
        # Tashqi havolalar (Instagram, YouTube, etc.) - tekshirmaslik
        if channel.get('is_external_link'):
            continue  # Tashqi havola - o'tkazib yuborish
        
        # So'rovli guruh uchun - database dan tekshirish
        if channel.get('is_request_group'):
            if has_join_request(user_id, channel_id):
                continue  # So'rov yuborilgan - OK
            else:
                return False  # So'rov yuborilmagan
        
        # Oddiy Telegram kanal uchun tekshirish
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception as e:
            print(f"Subscription check error: {e}")
            return False
    
    return True

async def show_subscription_message(message: Message, pending_movie_code: str = None):
    """Obuna bo'lish xabarini ko'rsatish"""
    channels = get_all_channels()
    channels_data = [{
        'title': ch['title'], 
        'url': ch['url'],
        'invite_link': ch.get('invite_link'),
        'is_request_group': ch.get('is_request_group'),
        'is_external_link': ch.get('is_external_link'),
        'channel_id': ch.get('channel_id'),
        'channel_username': ch.get('channel_username')
    } for ch in channels]
    
    # Callback data ga kino kodini qo'shish
    callback_data = f"check_sub_{pending_movie_code}" if pending_movie_code else "check_subscription"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for channel in channels_data:
        url = channel.get('invite_link') or channel.get('url') or f"https://t.me/{channel.get('channel_username', '')}"
        if channel.get('is_external_link'):
            btn_text = f"🔗 {channel.get('title', 'Obuna')}"
        else:
            btn_text = "➕ Kanalga obuna bo'lish"
        buttons.append([InlineKeyboardButton(text=btn_text, url=url)])
    buttons.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data=callback_data)])
    
    await message.answer(
        "❗️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


def get_movie_channel_button():
    """Kino uchun kanal tugmasini olish"""
    if not is_channel_button_enabled():
        return None
    
    btn_text = get_channel_button_text()
    btn_url = get_channel_button_url()
    
    if not btn_url:
        return None
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_text, url=btn_url)]
        ]
    )


async def send_movie_to_user(message: Message, movie, keyboard):
    """Foydalanuvchiga kinoni yuborish - baza kanaldan copy yoki file_id orqali"""
    
    # Kanal tugmasini olish
    channel_button = get_movie_channel_button()
    
    # Agar baza kanal va message_id mavjud bo'lsa - copy qilish
    if movie['base_channel_id'] and movie['message_id']:
        try:
            await message.bot.copy_message(
                chat_id=message.chat.id,
                from_chat_id=movie['base_channel_id'],
                message_id=movie['message_id'],
                reply_markup=channel_button  # Kanal tugmasi qo'shiladi
            )
            add_view(movie['id'], message.from_user.id)
            return True
        except Exception as e:
            # Agar copy qilib bo'lmasa, file_id orqali yuborish
            pass
    
    # File_id orqali yuborish (fallback)
    caption = movie['caption'] if movie['caption'] else f"🎬 {movie['title']}\n\n📥 Kod: {movie['code']}"
    await message.answer_video(
        video=movie['file_id'],
        caption=caption,
        reply_markup=channel_button if channel_button else movie_keyboard(movie['code'])
    )
    add_view(movie['id'], message.from_user.id)
    return True


@router.message(SearchMovie.waiting_for_query)
async def search_movie_handler(message: Message, state: FSMContext):
    """Qidiruv natijalari"""
    query = message.text.strip()
    
    # Bekor qilish tugmasi
    if query == "❌ Bekor qilish":
        await state.clear()
        keyboard = get_user_keyboard(message.from_user.id)
        await message.answer("❌ Qidiruv bekor qilindi.", reply_markup=keyboard)
        return
    
    # Boshqa tugmalarni tekshirish
    if query in ["🎬 Kino qidirish", "📊 Statistika", "ℹ️ Yordam", 
                 "☰ Menyu", "📺 Kanal boshqaruvi",
                 "🎬 Kino boshqaruvi", "📢 Xabar yuborish", "💎 Premium obuna",
                 "👑 Admin boshqaruvi", "🔗 Referal boshqaruvi", "⚙️ Bot sozlamlari"]:
        await state.clear()
        return
    
    # Obuna tekshirish (admin emas bo'lsa)
    if not is_admin(message.from_user.id):
        is_subscribed = await check_subscription(message.from_user.id, message.bot)
        if not is_subscribed:
            # Kino kodini tekshirish va pending qilish
            movie = get_movie_by_code(query)
            if movie:
                await show_subscription_message(message, query)  # Kino kodi bilan
            else:
                await show_subscription_message(message)
            return
    
    keyboard = get_user_keyboard(message.from_user.id)
    
    # Avval kod bo'yicha qidirish
    movie = get_movie_by_code(query)
    if movie:
        await send_movie_to_user(message, movie, keyboard)
        await state.clear()
        return
    
    # Nom bo'yicha qidirish
    movies = search_movies(query)
    if movies:
        text = f"🔍 <b>'{query}' bo'yicha natijalar:</b>\n\n"
        for m in movies:
            text += f"📥 Kod: <code>{m['code']}</code> - {m['title']}\n"
        text += "\n💡 Kinoni olish uchun kodini yuboring"
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(
            f"😔 '{query}' bo'yicha hech narsa topilmadi.\n\n"
            "Boshqa so'z bilan qidirib ko'ring.",
            reply_markup=keyboard
        )
    
    await state.clear()


@router.message(F.text)
async def any_text_handler(message: Message, state: FSMContext):
    """Har qanday matn - kino qidirish"""
    query = message.text.strip()
    
    # Tugmalarni o'tkazib yuborish
    if query in ["🎬 Kino qidirish", "📊 Statistika", "ℹ️ Yordam", 
                 "☰ Menyu", "❌ Bekor qilish", "📺 Kanal boshqaruvi",
                 "🎬 Kino boshqaruvi", "📢 Xabar yuborish", "💎 Premium obuna",
                 "👑 Admin boshqaruvi", "🔗 Referal boshqaruvi", "⚙️ Bot sozlamlari",
                 "📁 Baza kanal tanlash", "🔙 Orqaga qaytish", "💎 Premium obuna olish",
                 # Referal tugmalari
                 "💵 Referal - Pul ishlash", "🔗 Referal havolam", "💰 Hisobim",
                 "💳 Pul chiqarish", "📊 Statistikam", "📜 Tarix", "🔙 Asosiy menyu",
                 # Boshqa tugmalar
                 "🔔 Bildirishnomalar", "🌐 Til sozlamalari", "📌 Kino kodini yuboring"]:
        return
    
    # FSM holatini tekshirish - agar holat bo'lsa, boshqa handlerga qoldirish
    current_state = await state.get_state()
    if current_state:
        return
    
    # Obuna tekshirish (admin emas bo'lsa)
    if not is_admin(message.from_user.id):
        is_subscribed = await check_subscription(message.from_user.id, message.bot)
        if not is_subscribed:
            # Kino kodini tekshirish va pending qilish
            movie = get_movie_by_code(query)
            if movie:
                await show_subscription_message(message, query)  # Kino kodi bilan
            else:
                await show_subscription_message(message)
            return
    
    
    keyboard = get_user_keyboard(message.from_user.id)
    
    # Avval kod bo'yicha qidirish
    movie = get_movie_by_code(query)
    if movie:
        await send_movie_to_user(message, movie, keyboard)
        return
    
    # Nom bo'yicha qidirish
    movies = search_movies(query)
    if movies:
        text = f"🔍 <b>'{query}' bo'yicha natijalar:</b>\n\n"
        for m in movies:
            text += f"📥 Kod: <code>{m['code']}</code> - {m['title']}\n"
        text += "\n💡 Kinoni olish uchun kodini yuboring"
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(
            f"😔 '{query}' kodli yoki nomli kino topilmadi.\n\n"
            "💡 To'g'ri kod yoki nom kiritganingizni tekshiring.",
            reply_markup=keyboard
        )


@router.callback_query(F.data.startswith("check_sub_"))
async def check_subscription_with_movie_callback(callback: CallbackQuery):
    """Obunani tekshirish va kinoni yuborish"""
    # Kino kodini olish
    movie_code = callback.data.replace("check_sub_", "")
    
    # Obuna tekshirish
    is_subscribed = await check_subscription(callback.from_user.id, callback.bot)
    
    if is_subscribed:
        # Obuna tasdiqlandi - kinoni yuborish
        try:
            await callback.message.delete()
        except:
            pass
        
        movie = get_movie_by_code(movie_code)
        if movie:
            keyboard = get_user_keyboard(callback.from_user.id)
            await send_movie_to_user(callback.message, movie, keyboard)
            await callback.answer("✅ Obuna tasdiqlandi!", show_alert=False)
        else:
            keyboard = get_user_keyboard(callback.from_user.id)
            await callback.message.answer(
                "✅ Obuna tasdiqlandi! Endi botdan foydalanishingiz mumkin.\n\n"
                "🔍 Kino kodini yoki nomini yuboring:",
                reply_markup=keyboard
            )
    else:
        # Hali obuna bo'lmagan
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
