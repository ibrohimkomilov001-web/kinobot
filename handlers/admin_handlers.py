from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ChatShared, ChatJoinRequest, FSInputFile
from aiogram.fsm.context import FSMContext

from database import (
    add_movie, delete_movie, get_movie_by_code, 
    get_movies_count, get_users_count, get_all_users, get_all_movies,
    get_all_channels, add_channel, delete_channel, get_channels_count,
    is_subscription_enabled, toggle_subscription, get_base_channel, set_base_channel,
    get_subscription_message, set_subscription_message,
    get_today_users, get_today_views, get_weekly_users, get_total_views,
    is_admin, add_admin, remove_admin, get_all_admins,
    is_channel_button_enabled, toggle_channel_button,
    get_channel_button_text, set_channel_button_text,
    get_channel_button_url, set_channel_button_url,
    # Premium funksiyalar
    add_premium_plan, get_all_premium_plans, get_premium_plan, delete_premium_plan,
    add_premium_request, get_pending_premium_requests, get_premium_request,
    approve_premium_request, reject_premium_request, is_premium_user,
    get_premium_users_count, is_premium_enabled, set_premium_enabled,
    get_payment_card, set_payment_card,
    # Kengaytirilgan statistika
    get_daily_stats, get_top_movies, get_active_users, get_monthly_stats,
    # Professional data analytics
    get_hourly_stats, get_peak_hours, get_growth_rate, get_retention_rate,
    get_user_activity_distribution, get_movie_genres_stats, get_conversion_funnel,
    get_daily_active_users, get_user_lifetime_value, get_weekly_comparison,
    get_new_vs_returning, get_avg_session_depth, get_trending_movies, get_overview_stats,
    # Admin huquqlari
    get_admin_permissions, update_admin_permission, has_permission
)
from keyboards import (
    admin_menu_keyboard, admin_panel_keyboard, cancel_reply_keyboard,
    movie_management_keyboard, channel_management_keyboard, statistics_keyboard,
    movies_list_keyboard, back_keyboard, confirm_keyboard, select_base_channel_keyboard,
    bot_settings_keyboard, channel_button_settings_keyboard, backup_keyboard,
    backup_list_keyboard, backup_action_keyboard
)
from states import (
    AddMovie, DeleteMovie, Broadcast, AddChannel, AddChannelLink, 
    AddRequestGroup, SetBaseChannel, EditSubscriptionMessage,
    AddPremiumPlan, PremiumPayment, SetPaymentCard, EditReferralMessage,
    SetReferralBonus, SetMinWithdrawal, EditStartMessage
)
import backup

router = Router()


# Huquq tekshirish yordamchi funksiya
def check_permission(user_id: int, permission: str) -> bool:
    """Admin huquqini tekshirish"""
    perms = get_admin_permissions(user_id)
    if not perms:
        return False
    if perms.get('is_super'):
        return True
    return perms.get(permission, False)


# ===== ADMIN PANEL =====

@router.message(F.text == "📊 Statistika")
async def admin_stats_reply_handler(message: Message, state: FSMContext):
    """Statistika - Reply keyboard - Professional Data Analytics"""
    if not is_admin(message.from_user.id):
        return
    if not check_permission(message.from_user.id, 'can_stats'):
        await message.answer("❌ Sizda bu bo'limga kirish huquqi yo'q!")
        return
    
    await state.clear()
    
    # Umumiy statistika
    overview = get_overview_stats()
    growth = get_growth_rate(7)
    retention = get_retention_rate(7)
    funnel = get_conversion_funnel()
    
    # O'sish ko'rsatkichi
    growth_emoji = "📈" if growth['growth_rate'] >= 0 else "📉"
    growth_sign = "+" if growth['growth_rate'] >= 0 else ""
    
    text = f"""
📊 <b>PROFESSIONAL DATA ANALYTICS</b>
━━━━━━━━━━━━━━━━━━━━━

👥 <b>Foydalanuvchilar:</b>
┣ Jami: <code>{overview['total_users']:,}</code>
┣ Bugun: <code>+{overview['today_users']}</code>
┣ Haftalik: <code>+{overview['weekly_users']}</code>
┗ 💎 Premium: <code>{funnel['premium_users']}</code> ({funnel['premium_rate']}%)

🎬 <b>Kontentlar:</b>
┣ Kinolar: <code>{overview['total_movies']:,}</code>
┗ O'rtacha ko'rishlar: <code>{overview['views_per_movie']}</code>/kino

👁 <b>Ko'rishlar:</b>
┣ Jami: <code>{overview['total_views']:,}</code>
┣ Bugun: <code>{overview['today_views']}</code>
┣ Haftalik: <code>{overview['weekly_views']}</code>
┗ O'rtacha/user: <code>{overview['avg_views_per_user']}</code>

{growth_emoji} <b>O'sish tezligi (7 kun):</b>
┗ <code>{growth_sign}{growth['growth_rate']}%</code> ({growth['previous']} → {growth['current']})

🔄 <b>Retention Rate:</b>
┗ <code>{retention['retention_rate']}%</code> ({retention['active']}/{retention['total']} faol)

� <b>Konversiya:</b>
┣ Ko'rganlar: <code>{funnel['view_rate']}%</code>
┣ Faollar (5+): <code>{funnel['engage_rate']}%</code>
┗ Premium: <code>{funnel['premium_rate']}%</code>

<i>Batafsil tahlil uchun quyidagi tugmalarni tanlang 👇</i>
"""
    await message.answer(text, reply_markup=statistics_keyboard(), parse_mode="HTML")


@router.message(F.text == "📺 Kanal boshqaruvi")
async def admin_channels_reply_handler(message: Message, state: FSMContext):
    """Kanal boshqaruvi - Reply keyboard"""
    if not is_admin(message.from_user.id):
        return
    if not check_permission(message.from_user.id, 'can_channels'):
        await message.answer("❌ Sizda bu bo'limga kirish huquqi yo'q!")
        return
    
    await state.clear()
    
    sub_enabled = is_subscription_enabled()
    channels_count = get_channels_count()
    channels = get_all_channels()
    
    status = "Yoqilgan ✅" if sub_enabled else "O'chirilgan ❌"
    
    text = f"""
📺 <b>Kanal boshqaruvi</b>

🔔 Majburiy obuna: <b>{status}</b>

"""
    
    if channels:
        text += "<b>Kanallar ro'yxati:</b>\n"
        for ch in channels:
            text += f"+ {ch['title']} (<code>{ch['channel_id']}</code>)\n"
    else:
        text += "Hech qanday majburiy obuna kanali yo'q.\n"
    
    text += "\n<i>Amalni tanlang:</i>"
    
    await message.answer(
        text,
        reply_markup=channel_management_keyboard(sub_enabled, channels_count),
        parse_mode="HTML"
    )


@router.message(F.text == "🎬 Kino boshqaruvi")
async def admin_movies_reply_handler(message: Message, state: FSMContext):
    """Kino boshqaruvi - Reply keyboard"""
    if not is_admin(message.from_user.id):
        return
    if not check_permission(message.from_user.id, 'can_movies'):
        await message.answer("❌ Sizda bu bo'limga kirish huquqi yo'q!")
        return
    
    await state.clear()
    
    movies_count = get_movies_count()
    base_channel = get_base_channel()
    
    text = f"""
🎬 <b>Kino boshqaruvi</b>

📊 Jami kinolar: <b>{movies_count}</b>
📁 Baza kanal: <code>{base_channel if base_channel else 'Sozlanmagan'}</code>

<i>Amalni tanlang:</i>
"""
    await message.answer(
        text, 
        reply_markup=movie_management_keyboard(movies_count, base_channel),
        parse_mode="HTML"
    )


@router.message(F.text == "📢 Xabar yuborish")
async def admin_broadcast_reply_handler(message: Message, state: FSMContext):
    """Xabar yuborish - Reply keyboard"""
    if not is_admin(message.from_user.id):
        return
    if not check_permission(message.from_user.id, 'can_broadcast'):
        await message.answer("❌ Sizda bu bo'limga kirish huquqi yo'q!")
        return
    
    await state.clear()
    users_count = get_users_count()
    
    from keyboards import broadcast_type_keyboard
    await message.answer(
        f"📢 <b>Xabar yuborish</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{users_count}</b>\n\n"
        "📝 Xabar turini tanlang:",
        reply_markup=broadcast_type_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "💎 Premium obuna")
async def admin_premium_reply_handler(message: Message, state: FSMContext):
    """Premium - Reply keyboard"""
    if not is_admin(message.from_user.id):
        return
    if not check_permission(message.from_user.id, 'can_premium'):
        await message.answer("❌ Sizda bu bo'limga kirish huquqi yo'q!")
        return
    
    await state.clear()
    
    from keyboards import premium_management_keyboard
    enabled = is_premium_enabled()
    premium_count = get_premium_users_count()
    pending = len(get_pending_premium_requests())
    plans = get_all_premium_plans()
    card = get_payment_card()
    
    text = f"""
💎 <b>Premium Obuna Boshqaruvi</b>

📊 <b>Statistika:</b>
+ Premium foydalanuvchilar: <code>{premium_count}</code>
+ Kutilayotgan so'rovlar: <code>{pending}</code>
L Tariflar soni: <code>{len(plans)}</code>

💳 <b>To'lov kartasi:</b> <code>{card if card else "Sozlanmagan"}</code>
"""
    await message.answer(text, reply_markup=premium_management_keyboard(enabled), parse_mode="HTML")


@router.message(F.text == "👑 Admin boshqaruvi")
async def admin_admins_reply_handler(message: Message):
    """Admin boshqaruvi - Reply keyboard"""
    if not is_admin(message.from_user.id):
        return
    if not check_permission(message.from_user.id, 'can_admins'):
        await message.answer("❌ Sizda bu bo'limga kirish huquqi yo'q!")
        return
    
    from config import ADMINS
    from keyboards import admin_management_keyboard
    db_admins = get_all_admins()
    all_admins = list(set(ADMINS + db_admins))
    
    text = f"""
👑 <b>Adminlar boshqaruvi</b>

📊 <b>Statistika:</b>
+ Jami adminlar: <code>{len(all_admins)}</code>
+ Config adminlar: <code>{len(ADMINS)}</code>
L Qo'shilgan adminlar: <code>{len(db_admins)}</code>
"""
    
    await message.answer(text, reply_markup=admin_management_keyboard(), parse_mode="HTML")


@router.message(F.text == "🔗 Referal boshqaruvi")
async def admin_referral_reply_handler(message: Message):
    """Referal - Reply keyboard"""
    if not is_admin(message.from_user.id):
        return
    
    from database import (
        is_referral_enabled, get_referral_bonus, get_min_withdrawal,
        get_total_referral_stats, get_pending_withdrawals
    )
    from keyboards import referral_admin_keyboard
    
    is_enabled = is_referral_enabled()
    bonus = get_referral_bonus()
    min_withdrawal = get_min_withdrawal()
    stats = get_total_referral_stats()
    pending = get_pending_withdrawals()
    
    status = "🟢 Yoniq" if is_enabled else "🔴 O'chiq"
    
    text = f"""
🔗 <b>Referal boshqaruvi</b>

📊 <b>Holat:</b> {status}

⚙️ <b>Sozlamalar:</b>
+ Har bir referal: <b>{bonus:,} so'm</b>
L Min. chiqarish: <b>{min_withdrawal:,} so'm</b>

📊 <b>Statistika:</b>
+ Jami referallar: <b>{stats['total_referrals']}</b>
+ Berilgan bonuslar: <b>{stats['total_bonuses']:,} so'm</b>
+ Chiqarilgan pul: <b>{stats['total_withdrawn']:,} so'm</b>
L Kutilayotgan so'rovlar: <b>{stats['pending_requests']}</b>
"""
    
    await message.answer(text, reply_markup=referral_admin_keyboard(), parse_mode="HTML")


@router.message(F.text == "⚙️ Bot sozlamlari")
async def admin_settings_reply_handler(message: Message):
    """Sozlamalar - Reply keyboard"""
    if not is_admin(message.from_user.id):
        return
    
    from database import get_base_channel, get_start_media
    
    base_channel = get_base_channel()
    start_media = get_start_media()
    
    text = "⚙️ <b>Bot sozlamalari</b>\n\n"
    
    # Baza kanal
    if base_channel:
        text += f"📁 <b>Baza kanal:</b> <code>{base_channel}</code>\n"
    else:
        text += "📁 <b>Baza kanal:</b> ❌ Tanlanmagan\n"
    
    # Start xabari media
    if start_media:
        media_type = "🖼 Rasm" if start_media['type'] == 'photo' else "🎬 GIF"
        text += f"📝 <b>Start xabari:</b> {media_type} + Matn\n"
    else:
        text += "📝 <b>Start xabari:</b> Faqat matn\n"
    
    text += "\n👇 Quyidagi tugmalardan birini tanlang:"
    
    await message.answer(
        text, 
        reply_markup=bot_settings_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "📝 Start xabarini tahrirlash")
async def edit_start_message_reply_handler(message: Message):
    """Start xabarini tahrirlash - Reply"""
    if not is_admin(message.from_user.id):
        return
    
    from database import get_start_message, get_start_media
    from keyboards import start_message_keyboard
    
    current_message = get_start_message()
    start_media = get_start_media()
    has_media = start_media is not None
    
    text = "📝 <b>Start xabarini tahrirlash</b>\n\n"
    text += f"<b>Hozirgi xabar:</b>\n<i>{current_message}</i>\n\n"
    
    if has_media:
        media_type = "🖼 Rasm" if start_media['type'] == 'photo' else "🎬 GIF"
        text += f"<b>Media:</b> {media_type} mavjud\n\n"
    
    text += "Quyidagi tugmalardan birini tanlang:"
    
    await message.answer(text, reply_markup=start_message_keyboard(has_media), parse_mode="HTML")


@router.message(F.text == "🔙 Orqaga qaytish")
async def back_to_admin_menu_reply_handler(message: Message):
    """Admin menyuga qaytish - Reply keyboard"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "👋 <b>Admin panel</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "🔔 Bildirishnomalar")
async def notifications_handler(message: Message):
    """Bildirishnomalar sozlamalari"""
    if not is_admin(message.from_user.id):
        return
    await message.answer("🔔 Bildirishnomalar sozlamalari tez orada!")


@router.message(F.text == "🌐 Til sozlamalari")
async def language_settings_handler(message: Message):
    """Til sozlamalari"""
    if not is_admin(message.from_user.id):
        return
    await message.answer("🌐 Til sozlamalari tez orada!")


# ===== START XABARI TAHRIRLASH =====

@router.callback_query(F.data == "edit_start_message")
async def edit_start_message_callback(callback: CallbackQuery):
    """Start xabarini tahrirlash - Callback"""
    if not is_admin(callback.from_user.id):
        return
    
    from database import get_start_message, get_start_media
    from keyboards import start_message_keyboard
    
    current_message = get_start_message()
    start_media = get_start_media()
    has_media = start_media is not None
    
    text = "📝 <b>Start xabarini tahrirlash</b>\n\n"
    text += f"<b>Hozirgi xabar:</b>\n<i>{current_message}</i>\n\n"
    
    if has_media:
        media_type = "🖼 Rasm" if start_media['type'] == 'photo' else "🎬 GIF"
        text += f"<b>Media:</b> {media_type} mavjud\n\n"
    
    text += "Quyidagi tugmalardan birini tanlang:"
    
    await callback.message.edit_text(text, reply_markup=start_message_keyboard(has_media), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_bot_settings")
async def admin_bot_settings_callback(callback: CallbackQuery):
    """Bot sozlamalariga qaytish - Callback"""
    if not is_admin(callback.from_user.id):
        return
    
    from database import get_base_channel, get_start_media
    
    base_channel = get_base_channel()
    start_media = get_start_media()
    
    text = "⚙️ <b>Bot sozlamalari</b>\n\n"
    
    if base_channel:
        text += f"📁 <b>Baza kanal:</b> <code>{base_channel}</code>\n"
    else:
        text += "📁 <b>Baza kanal:</b> ❌ Tanlanmagan\n"
    
    if start_media:
        media_type = "🖼 Rasm" if start_media['type'] == 'photo' else "🎬 GIF"
        text += f"📝 <b>Start xabari:</b> {media_type} + Matn\n"
    else:
        text += "📝 <b>Start xabari:</b> Faqat matn\n"
    
    # Inline xabarni o'chirish va reply keyboard bilan yangi xabar yuborish
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=bot_settings_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "edit_start_text")
async def edit_start_text_callback(callback: CallbackQuery, state: FSMContext):
    """Start xabari matnini tahrirlash"""
    if not is_admin(callback.from_user.id):
        return
    
    from states import EditStartMessage
    from database import get_start_message
    
    current = get_start_message()
    
    await state.set_state(EditStartMessage.waiting_for_content)
    await state.update_data(content_type='text')
    
    await callback.message.edit_text(
        f"📝 <b>Start xabari matnini kiriting</b>\n\n"
        f"<b>Hozirgi:</b>\n<i>{current}</i>\n\n"
        f"HTML formatini ishlatishingiz mumkin:\n"
        f"<code>&lt;b&gt;qalin&lt;/b&gt;</code>\n"
        f"<code>&lt;i&gt;kursiv&lt;/i&gt;</code>\n"
        f"<code>&lt;code&gt;kod&lt;/code&gt;</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "edit_start_photo")
async def edit_start_photo_callback(callback: CallbackQuery, state: FSMContext):
    """Start xabari rasmini tahrirlash"""
    if not is_admin(callback.from_user.id):
        return
    
    from states import EditStartMessage
    
    await state.set_state(EditStartMessage.waiting_for_content)
    await state.update_data(content_type='photo')
    
    await callback.message.edit_text(
        "🖼 <b>Rasm yuklang</b>\n\n"
        "Rasm bilan birga caption (matn) ham yozishingiz mumkin.\n"
        "Bu matn start xabarining matni bo'ladi.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "edit_start_gif")
async def edit_start_gif_callback(callback: CallbackQuery, state: FSMContext):
    """Start xabari GIF tahrirlash"""
    if not is_admin(callback.from_user.id):
        return
    
    from states import EditStartMessage
    
    await state.set_state(EditStartMessage.waiting_for_content)
    await state.update_data(content_type='gif')
    
    await callback.message.edit_text(
        "🎬 <b>GIF yuklang</b>\n\n"
        "GIF bilan birga caption (matn) ham yozishingiz mumkin.\n"
        "Bu matn start xabarining matni bo'ladi.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "delete_start_media")
async def delete_start_media_callback(callback: CallbackQuery):
    """Start xabari mediasini o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    
    from database import delete_start_media, get_start_message
    from keyboards import start_message_keyboard
    
    delete_start_media()
    
    current_message = get_start_message()
    
    text = "✅ <b>Media o'chirildi!</b>\n\n"
    text += f"<b>Hozirgi xabar:</b>\n<i>{current_message}</i>\n\n"
    text += "Quyidagi tugmalardan birini tanlang:"
    
    await callback.message.edit_text(text, reply_markup=start_message_keyboard(False), parse_mode="HTML")
    await callback.answer("Media o'chirildi!")


@router.callback_query(F.data == "preview_start_message")
async def preview_start_message_callback(callback: CallbackQuery):
    """Start xabarini ko'rish"""
    if not is_admin(callback.from_user.id):
        return
    
    from database import get_start_message, get_start_media
    from keyboards import start_message_keyboard
    
    message_text = get_start_message()
    start_media = get_start_media()
    
    try:
        if start_media:
            if start_media['type'] == 'photo':
                await callback.message.answer_photo(
                    photo=start_media['file_id'],
                    caption=message_text,
                    parse_mode="HTML"
                )
            else:  # animation/gif
                await callback.message.answer_animation(
                    animation=start_media['file_id'],
                    caption=message_text,
                    parse_mode="HTML"
                )
        else:
            await callback.message.answer(message_text, parse_mode="HTML")
        
        await callback.answer("👁 Start xabari yuqorida ko'rsatildi")
    except Exception as e:
        await callback.answer(f"Xatolik: {str(e)}", show_alert=True)


@router.message(F.chat_shared)
async def handle_base_channel_selection(message: Message):
    """Baza kanal tanlash - chat_shared orqali"""
    if not is_admin(message.from_user.id):
        return
    
    chat_shared = message.chat_shared
    channel_id = chat_shared.chat_id
    
    # Kanal ma'lumotlarini olish
    try:
        chat = await message.bot.get_chat(channel_id)
        title = chat.title
        
        # Botning admin ekanligini tekshirish
        bot_member = await message.bot.get_chat_member(channel_id, message.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.answer(
                "⚠️ Bot bu kanalda admin emas!\n\n"
                "Botni kanalga admin qilib qo'shing va qaytadan urinib ko'ring.",
                reply_markup=bot_settings_keyboard()
            )
            return
            
    except Exception as e:
        title = f"Kanal"
        
    set_base_channel(str(channel_id))
    
    await message.answer(
        f"✅ Baza kanal muvaffaqiyatli yangilandi!\n\n"
        f"📺 Kanal: <b>{title}</b>\n"
        f"🆔 ID: <code>{channel_id}</code>\n\n"
        f"Endi kinolar shu kanalga yuklanadi.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_admin")
async def back_to_admin_handler(callback: CallbackQuery, state: FSMContext):
    """Admin panelga qaytish"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.clear()
    
    users_count = get_users_count()
    movies_count = get_movies_count()
    
    text = f"""
👑 <b>Admin Panel</b>

👥 Foydalanuvchilar: <b>{users_count}</b>
🎬 Kinolar: <b>{movies_count}</b>
"""
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer("✅ Asosiy menyuga qaytdingiz")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery, state: FSMContext):
    """Asosiy menyuga qaytish"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("📋 Asosiy menyu:", reply_markup=admin_menu_keyboard())
    await callback.answer()


# ===== STATISTIKA =====

@router.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: CallbackQuery):
    """Statistika bo'limi - Professional Analytics"""
    if not is_admin(callback.from_user.id):
        return
    
    # Umumiy statistika
    overview = get_overview_stats()
    growth = get_growth_rate(7)
    retention = get_retention_rate(7)
    funnel = get_conversion_funnel()
    
    # O'sish ko'rsatkichi
    growth_emoji = "📈" if growth['growth_rate'] >= 0 else "📉"
    growth_sign = "+" if growth['growth_rate'] >= 0 else ""
    
    text = f"""
📊 <b>PROFESSIONAL DATA ANALYTICS</b>
━━━━━━━━━━━━━━━━━━━━━

👥 <b>Foydalanuvchilar:</b>
┣ Jami: <code>{overview['total_users']:,}</code>
┣ Bugun: <code>+{overview['today_users']}</code>
┣ Haftalik: <code>+{overview['weekly_users']}</code>
┗ 💎 Premium: <code>{funnel['premium_users']}</code> ({funnel['premium_rate']}%)

🎬 <b>Kontentlar:</b>
┣ Kinolar: <code>{overview['total_movies']:,}</code>
┗ O'rtacha ko'rishlar: <code>{overview['views_per_movie']}</code>/kino

👁 <b>Ko'rishlar:</b>
┣ Jami: <code>{overview['total_views']:,}</code>
┣ Bugun: <code>{overview['today_views']}</code>
┣ Haftalik: <code>{overview['weekly_views']}</code>
┗ O'rtacha/user: <code>{overview['avg_views_per_user']}</code>

{growth_emoji} <b>O'sish tezligi (7 kun):</b>
┗ <code>{growth_sign}{growth['growth_rate']}%</code>

🔄 <b>Retention Rate:</b>
┗ <code>{retention['retention_rate']}%</code>

<i>Batafsil tahlil uchun tugmalarni tanlang 👇</i>
"""
    await callback.message.edit_text(text, reply_markup=statistics_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_overview")
async def stats_overview_handler(callback: CallbackQuery):
    """Umumiy ko'rsatkichlar - batafsil"""
    if not is_admin(callback.from_user.id):
        return
    
    overview = get_overview_stats()
    funnel = get_conversion_funnel()
    daily = get_daily_stats(7)
    
    # Haftalik grafik
    graph = ""
    max_val = max([d['new_users'] for d in daily]) if daily else 1
    for day in reversed(daily):
        bar_len = int((day['new_users'] / max(max_val, 1)) * 10)
        bar = "█" * bar_len + "░" * (10 - bar_len)
        graph += f"┃ {day['date'][5:]} {bar} {day['new_users']}\n"
    
    text = f"""
📊 <b>UMUMIY KO'RSATKICHLAR</b>
━━━━━━━━━━━━━━━━━━━━━

<b>📈 Asosiy raqamlar:</b>
┣ 👥 Foydalanuvchilar: <code>{overview['total_users']:,}</code>
┣ 🎬 Kinolar: <code>{overview['total_movies']:,}</code>
┣ 👁 Ko'rishlar: <code>{overview['total_views']:,}</code>
┗ 💎 Premium: <code>{funnel['premium_users']}</code>

<b>📅 Bugungi natijalar:</b>
┣ Yangi foydalanuvchilar: <code>+{overview['today_users']}</code>
┗ Ko'rishlar: <code>{overview['today_views']}</code>

<b>📊 Haftalik natijalar:</b>
┣ Yangi foydalanuvchilar: <code>+{overview['weekly_users']}</code>
┗ Ko'rishlar: <code>{overview['weekly_views']}</code>

<b>📉 Haftalik o'sish grafigi:</b>
<code>
{graph}</code>

<b>📏 O'rtacha ko'rsatkichlar:</b>
┣ Ko'rishlar/foydalanuvchi: <code>{overview['avg_views_per_user']}</code>
┗ Ko'rishlar/kino: <code>{overview['views_per_movie']}</code>
"""
    await callback.message.edit_text(text, reply_markup=statistics_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_users")
async def stats_users_handler(callback: CallbackQuery):
    """Foydalanuvchilar analitikasi"""
    if not is_admin(callback.from_user.id):
        return
    
    distribution = get_user_activity_distribution()
    new_vs_ret = get_new_vs_returning()
    retention = get_retention_rate(7)
    growth = get_growth_rate(7)
    
    total = sum(distribution.values())
    
    text = f"""
� <b>FOYDALANUVCHILAR ANALITIKASI</b>
━━━━━━━━━━━━━━━━━━━━━

<b>�📊 Faollik bo'yicha taqsimot:</b>
┣ 😴 Passiv (0 ko'rish): <code>{distribution['passive']}</code> ({round(distribution['passive']/max(total,1)*100, 1)}%)
┣ 🌱 Yengil (1-5): <code>{distribution['light']}</code> ({round(distribution['light']/max(total,1)*100, 1)}%)
┣ 🌿 O'rtacha (6-20): <code>{distribution['medium']}</code> ({round(distribution['medium']/max(total,1)*100, 1)}%)
┣ 🌳 Faol (21-50): <code>{distribution['active']}</code> ({round(distribution['active']/max(total,1)*100, 1)}%)
┗ � Super faol (50+): <code>{distribution['super_active']}</code> ({round(distribution['super_active']/max(total,1)*100, 1)}%)

<b>🔄 Yangi vs Qaytuvchi (7 kun):</b>
┣ 🆕 Yangi faollar: <code>{new_vs_ret['new_active']}</code>
┣ 🔁 Qaytib kelganlar: <code>{new_vs_ret['returning_active']}</code>
┗ 📊 Jami faol: <code>{new_vs_ret['total_active']}</code>

<b>📈 O'sish ko'rsatkichlari:</b>
┣ Haftalik o'sish: <code>{'+' if growth['growth_rate'] >= 0 else ''}{growth['growth_rate']}%</code>
┗ Retention rate: <code>{retention['retention_rate']}%</code>

<i>💡 Tavsiya: Passiv foydalanuvchilarga xabar yuborib, faollashtiring!</i>
"""
    await callback.message.edit_text(text, reply_markup=statistics_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_movies")
async def stats_movies_handler(callback: CallbackQuery):
    """Kinolar analitikasi"""
    if not is_admin(callback.from_user.id):
        return
    
    top_movies = get_top_movies(10)
    genres = get_movie_genres_stats()
    trending = get_trending_movies(7, 5)
    
    # Top kinolar ro'yxati
    top_list = ""
    for i, m in enumerate(top_movies[:10], 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        title = m['title'][:20] + "..." if len(m['title']) > 20 else m['title']
        top_list += f"{medal} <code>{m['code']}</code> - {title} ({m['views']})\n"
    
    # Janrlar
    genre_list = ""
    for g in genres[:5]:
        genre_list += f"┣ {g['genre']}: {g['movies']} kino, {g['views']} ko'rish\n"
    
    # Trend kinolar
    trend_list = ""
    for t in trending:
        title = t['title'][:18] + ".." if len(t['title']) > 18 else t['title']
        trend_list += f"┣ 🔥 {title} (+{t['recent_views']})\n"
    
    text = f"""
🎬 <b>KINOLAR ANALITIKASI</b>
━━━━━━━━━━━━━━━━━━━━━

<b>🏆 Top 10 kinolar:</b>
{top_list}
<b>🎭 Janrlar bo'yicha:</b>
{genre_list if genre_list else "Ma'lumot yo'q"}

<b>🔥 Trend kinolar (7 kun):</b>
{trend_list if trend_list else "Ma'lumot yo'q"}
"""
    await callback.message.edit_text(text, reply_markup=statistics_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_growth")
async def stats_growth_handler(callback: CallbackQuery):
    """O'sish tezligi analitikasi"""
    if not is_admin(callback.from_user.id):
        return
    
    growth_7 = get_growth_rate(7)
    growth_30 = get_growth_rate(30)
    daily = get_daily_stats(14)
    
    # Haftalik grafik
    graph = ""
    max_val = max([d['new_users'] for d in daily]) if daily else 1
    for day in reversed(daily):
        bar_len = int((day['new_users'] / max(max_val, 1)) * 15)
        bar = "█" * bar_len
        graph += f"{day['date'][5:]} {bar} {day['new_users']}\n"
    
    g7_emoji = "📈" if growth_7['growth_rate'] >= 0 else "📉"
    g30_emoji = "📈" if growth_30['growth_rate'] >= 0 else "📉"
    
    text = f"""
📈 <b>O'SISH TEZLIGI ANALITIKASI</b>
━━━━━━━━━━━━━━━━━━━━━

<b>{g7_emoji} Haftalik o'sish:</b>
┣ Bu hafta: <code>{growth_7['current']}</code> yangi foydalanuvchi
┣ O'tgan hafta: <code>{growth_7['previous']}</code>
┗ Farq: <code>{'+' if growth_7['growth_rate'] >= 0 else ''}{growth_7['growth_rate']}%</code>

<b>{g30_emoji} Oylik o'sish:</b>
┣ Bu oy: <code>{growth_30['current']}</code> yangi foydalanuvchi
┣ O'tgan oy: <code>{growth_30['previous']}</code>
┗ Farq: <code>{'+' if growth_30['growth_rate'] >= 0 else ''}{growth_30['growth_rate']}%</code>

<b>📊 14 kunlik grafik:</b>
<code>
{graph}</code>
"""
    await callback.message.edit_text(text, reply_markup=statistics_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_retention")
async def stats_retention_handler(callback: CallbackQuery):
    """Retention analitikasi"""
    if not is_admin(callback.from_user.id):
        return
    
    ret_7 = get_retention_rate(7)
    ret_30 = get_retention_rate(30)
    new_vs_ret = get_new_vs_returning()
    avg_depth = get_avg_session_depth()
    
    text = f"""
🔄 <b>RETENTION ANALITIKASI</b>
━━━━━━━━━━━━━━━━━━━━━

<b>📊 Qaytib kelish ko'rsatkichi:</b>
┣ 7 kunlik: <code>{ret_7['retention_rate']}%</code>
┃   ({ret_7['active']} faol / {ret_7['total']} jami)
┗ 30 kunlik: <code>{ret_30['retention_rate']}%</code>
    ({ret_30['active']} faol / {ret_30['total']} jami)

<b>🆕 Yangi vs Qaytuvchi (7 kun):</b>
┣ Yangi foydalanuvchilar: <code>{new_vs_ret['new_active']}</code>
┣ Qaytib kelganlar: <code>{new_vs_ret['returning_active']}</code>
┗ Jami faol: <code>{new_vs_ret['total_active']}</code>

<b>� Sessiya chuqurligi:</b>
┗ O'rtacha: <code>{avg_depth}</code> kino/tashrif

<i>💡 Retention - foydalanuvchilar qanchalik qaytib kelishini ko'rsatadi</i>
"""
    await callback.message.edit_text(text, reply_markup=statistics_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_time")
async def stats_time_handler(callback: CallbackQuery):
    """Vaqt analitikasi"""
    if not is_admin(callback.from_user.id):
        return
    
    peak_hours = get_peak_hours(7)
    weekly_comp = get_weekly_comparison()
    
    # Peak soatlar
    peak_list = ""
    for p in peak_hours:
        hour = f"{p['hour']:02d}:00"
        bar_len = min(int(p['count'] / 10), 10)
        bar = "█" * bar_len
        peak_list += f"┣ {hour} {bar} {p['count']}\n"
    
    # Hafta kunlari
    week_list = ""
    for w in weekly_comp:
        week_list += f"┣ {w['day']}: {w['views']} ko'rish\n"
    
    text = f"""
⏰ <b>VAQT ANALITIKASI</b>
━━━━━━━━━━━━━━━━━━━━━

<b>🕐 Eng faol soatlar (7 kun):</b>
{peak_list if peak_list else "Ma'lumot yo'q"}

<b>📅 Hafta kunlari bo'yicha:</b>
{week_list if week_list else "Ma'lumot yo'q"}

<i>💡 Bu ma'lumotlar xabar yuborish vaqtini tanlashda yordam beradi!</i>
"""
    await callback.message.edit_text(text, reply_markup=statistics_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_trends")
async def stats_trends_handler(callback: CallbackQuery):
    """Trend analitikasi"""
    if not is_admin(callback.from_user.id):
        return
    
    trending = get_trending_movies(7, 10)
    
    trend_list = ""
    for i, t in enumerate(trending, 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        title = t['title'][:22] + ".." if len(t['title']) > 22 else t['title']
        trend_list += f"{medal} <code>{t['code']}</code>\n   {title}\n   📊 Haftalik: {t['recent_views']} | Jami: {t['total_views']}\n\n"
    
    text = f"""
🔥 <b>TREND KINOLAR</b>
━━━━━━━━━━━━━━━━━━━━━
<i>Oxirgi 7 kunda eng ko'p ko'rilganlar</i>

{trend_list if trend_list else "Hali trend kinolar yo'q"}
"""
    await callback.message.edit_text(text, reply_markup=statistics_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_funnel")
async def stats_funnel_handler(callback: CallbackQuery):
    """Konversiya voronkasi"""
    if not is_admin(callback.from_user.id):
        return
    
    funnel = get_conversion_funnel()
    
    # Voronka grafigi
    def bar(pct):
        filled = int(pct / 5)
        return "█" * filled + "░" * (20 - filled)
    
    text = f"""
📉 <b>KONVERSIYA VORONKASI</b>
━━━━━━━━━━━━━━━━━━━━━

<b>Bosqichlar:</b>

1️⃣ <b>Jami foydalanuvchilar</b>
   {bar(100)} 100%
   <code>{funnel['total_users']:,}</code> kishi

2️⃣ <b>Kamida 1 kino ko'rganlar</b>
   {bar(funnel['view_rate'])} {funnel['view_rate']}%
   <code>{funnel['viewed_users']:,}</code> kishi

3️⃣ <b>Faol foydalanuvchilar (5+ kino)</b>
   {bar(funnel['engage_rate'] * funnel['view_rate'] / 100)} {round(funnel['engage_rate'] * funnel['view_rate'] / 100, 1)}%
   <code>{funnel['engaged_users']:,}</code> kishi

4️⃣ <b>💎 Premium obunachilari</b>
   {bar(funnel['premium_rate'])} {funnel['premium_rate']}%
   <code>{funnel['premium_users']:,}</code> kishi

<i>💡 Har bir bosqichni yaxshilash konversiyani oshiradi!</i>
"""
    await callback.message.edit_text(text, reply_markup=statistics_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "stats_top_users")
async def stats_top_users_handler(callback: CallbackQuery):
    """Top foydalanuvchilar"""
    if not is_admin(callback.from_user.id):
        return
    
    top_users = get_user_lifetime_value()
    
    user_list = ""
    for i, u in enumerate(top_users[:15], 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        name = u['full_name'][:15] + ".." if len(u['full_name']) > 15 else u['full_name']
        premium = "💎" if u['is_premium'] else ""
        username = f"@{u['username']}" if u['username'] else ""
        user_list += f"{medal} {premium}<b>{name}</b> {username}\n    ID: <code>{u['user_id']}</code> | Ko'rishlar: {u['total_views']}\n"
    
    text = f"""
👑 <b>TOP FOYDALANUVCHILAR</b>
━━━━━━━━━━━━━━━━━━━━━
<i>Eng ko'p kino ko'rgan foydalanuvchilar</i>

{user_list if user_list else "Hali ma'lumot yo'q"}
"""
    await callback.message.edit_text(text, reply_markup=statistics_keyboard(), parse_mode="HTML")
    await callback.answer()


# ===== KINO BOSHQARUVI =====

@router.callback_query(F.data == "admin_movies")
async def admin_movies_handler(callback: CallbackQuery):
    """Kino boshqaruvi"""
    if not is_admin(callback.from_user.id):
        return
    
    movies_count = get_movies_count()
    base_channel = get_base_channel()
    
    text = f"""
🎬 <b>Kino boshqaruvi</b>

📊 Jami kinolar: <b>{movies_count}</b>
📁 Baza kanal: <code>{base_channel if base_channel else 'Sozlanmagan'}</code>

<i>Amalni tanlang:</i>
"""
    await callback.message.edit_text(
        text, 
        reply_markup=movie_management_keyboard(movies_count, base_channel),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "movie_management")
async def movie_management_back_handler(callback: CallbackQuery):
    """Kino boshqaruviga qaytish"""
    if not is_admin(callback.from_user.id):
        return
    
    movies_count = get_movies_count()
    base_channel = get_base_channel()
    
    text = f"""🎬 <b>Kino boshqaruvi</b>

📊 Jami kinolar: <b>{movies_count}</b>
📁 Baza kanal: <code>{base_channel if base_channel else 'Sozlanmagan'}</code>

<i>Amalni tanlang:</i>
"""
    await callback.message.edit_text(
        text, 
        reply_markup=movie_management_keyboard(movies_count, base_channel),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "movies_list")
async def movies_list_handler(callback: CallbackQuery):
    """Kinolar ro'yxati"""
    if not is_admin(callback.from_user.id):
        return
    
    movies = get_all_movies()
    
    if not movies:
        await callback.answer("📋 Kinolar ro'yxati bo'sh!", show_alert=True)
        return
    
    movies_data = [{'code': m['code'], 'title': m['title']} for m in movies]
    
    text = f"📋 <b>Kinolar ro'yxati</b>\n\nJami: {len(movies)} ta kino"
    
    await callback.message.edit_text(
        text,
        reply_markup=movies_list_keyboard(movies_data, page=1),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("movies_page_"))
async def movies_page_handler(callback: CallbackQuery):
    """Kinolar sahifalash"""
    if not is_admin(callback.from_user.id):
        return
    
    page = int(callback.data.split("_")[-1])
    movies = get_all_movies()
    movies_data = [{'code': m['code'], 'title': m['title']} for m in movies]
    
    text = f"📋 <b>Kinolar ro'yxati</b>\n\nJami: {len(movies)} ta kino"
    
    await callback.message.edit_text(
        text,
        reply_markup=movies_list_keyboard(movies_data, page=page),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "movie_add")
async def movie_add_handler(callback: CallbackQuery, state: FSMContext):
    """Kino qo'shishni boshlash - 1. Video yuborish"""
    if not is_admin(callback.from_user.id):
        return
    
    # Baza kanalni tekshirish
    base_channel = get_base_channel()
    if not base_channel:
        await callback.message.answer(
            "⚠️ Baza kanal sozlanmagan!\n\n"
            "Avval ⚙️ Bot sozlamalari > 📁 Baza kanal tanlash orqali baza kanalni tanlang.",
            reply_markup=admin_menu_keyboard()
        )
        await callback.answer()
        return
    
    await state.set_state(AddMovie.waiting_for_video)
    await callback.message.answer(
        "🎬 <b>Kino qo'shish</b>\n\n"
        "1️⃣ Kinoni (video) yuboring:",
        reply_markup=cancel_reply_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddMovie.waiting_for_video, F.video)
async def add_movie_video(message: Message, state: FSMContext):
    """1. Kino videosi qabul qilish"""
    video = message.video
    
    # Video davomiyligini olish va format qilish
    duration_seconds = video.duration if video.duration else 0
    hours = duration_seconds // 3600
    minutes = (duration_seconds % 3600) // 60
    seconds = duration_seconds % 60
    
    if hours > 0:
        duration_text = f"{hours} soat {minutes} daqiqa"
    elif minutes > 0:
        duration_text = f"{minutes} daqiqa {seconds} soniya"
    else:
        duration_text = f"{seconds} soniya"
    
    await state.update_data(
        file_id=video.file_id,
        duration=duration_text
    )
    
    await state.set_state(AddMovie.waiting_for_title)
    await message.answer(
        "✅ Video qabul qilindi!\n\n"
        "2️⃣ Film nomini kiriting:",
        parse_mode="HTML"
    )


@router.message(AddMovie.waiting_for_video)
async def add_movie_video_invalid(message: Message, state: FSMContext):
    """Noto'g'ri format - video kutilmoqda"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    await message.answer("⚠️ Iltimos, video faylni yuboring!")


@router.message(AddMovie.waiting_for_title)
async def add_movie_title(message: Message, state: FSMContext):
    """2. Film nomi"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovie.waiting_for_genre)
    await message.answer(
        "✅ Film nomi qabul qilindi!\n\n"
        "3️⃣ Film janrini kiriting:\n"
        "<i>Masalan: Drama, Jangari, Komediya, Triller</i>",
        parse_mode="HTML"
    )


@router.message(AddMovie.waiting_for_genre)
async def add_movie_genre(message: Message, state: FSMContext):
    """3. Film janri"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    await state.update_data(genre=message.text.strip())
    await state.set_state(AddMovie.waiting_for_code)
    await message.answer(
        "✅ Janr qabul qilindi!\n\n"
        "4️⃣ Kino kodini kiriting (faqat raqamlar):\n"
        "<i>Masalan: 123, 1001, 5050</i>",
        parse_mode="HTML"
    )


@router.message(AddMovie.waiting_for_code)
async def add_movie_code(message: Message, state: FSMContext):
    """4. Kino kodi - oxirgi qadam"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    code = message.text.strip()
    
    # Kod mavjudligini tekshirish
    existing = get_movie_by_code(code)
    if existing:
        await message.answer(
            f"⚠️ Bu kod (<code>{code}</code>) allaqachon mavjud!\n"
            f"Kino nomi: {existing['title']}\n\n"
            "Boshqa kod kiriting:",
            parse_mode="HTML"
        )
        return
    
    data = await state.get_data()
    
    # Baza kanalni olish
    base_channel = get_base_channel()
    
    try:
        base_channel_id = int(base_channel)
    except ValueError:
        await message.answer(
            "❌ Baza kanal noto'g'ri sozlangan!",
            reply_markup=admin_menu_keyboard()
        )
        await state.clear()
        return
    
    # Bot ma'lumotlarini olish
    bot_info = await message.bot.me()
    bot_link = f"https://t.me/{bot_info.username}?start={code}"
    
    # Baza kanalga yuboriladigan caption - chiroyli shrift
    caption = (
        f"🎬 FILM: {data['title']}\n\n"
        f"🎭 Janr: {data['genre']}\n"
        f"⏱ Davomiylik: {data['duration']}\n"
        f"🔢 Kod: {code}\n\n"
        f"🤖 Bot orqali ko'ring: {bot_link}"
    )
    
    # Kinoni baza kanalga yuborish (tugmasiz)
    try:
        sent_message = await message.bot.send_video(
            chat_id=base_channel_id,
            video=data['file_id'],
            caption=caption
        )
        
        # Database ga saqlash
        from database import add_movie_with_message_id
        
        success = add_movie_with_message_id(
            code=code,
            title=data['title'],
            file_id=data['file_id'],
            genre=data['genre'],
            duration=data['duration'],
            caption=caption,
            added_by=message.from_user.id,
            base_channel_id=base_channel_id,
            message_id=sent_message.message_id
        )
        
        if success:
            await message.answer(
                f"✅ <b>Kino muvaffaqiyatli qo'shildi!</b>\n\n"
                f"🎬 Nomi: {data['title']}\n"
                f"🎭 Janr: {data['genre']}\n"
                f"⏱ Davomiyligi: {data['duration']}\n"
                f"🔢 Kod: <code>{code}</code>\n\n"
                f"✅ Baza kanalga yuklandi\n"
                f"🔗 Havola: {bot_link}",
                reply_markup=admin_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "❌ Database xatoligi. Qaytadan urinib ko'ring.",
                reply_markup=admin_menu_keyboard()
            )
            
    except Exception as e:
        await message.answer(
            f"❌ Baza kanalga yuborishda xatolik!\n\n"
            f"Sabab: Bot baza kanalda admin emas yoki kanal topilmadi.\n"
            f"Xatolik: {str(e)[:100]}",
            reply_markup=admin_menu_keyboard()
        )
    
    await state.clear()


@router.callback_query(F.data == "movie_delete")
async def movie_delete_handler(callback: CallbackQuery, state: FSMContext):
    """Kino o'chirishni boshlash"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.set_state(DeleteMovie.waiting_for_code)
    await callback.message.answer(
        "🗑 O'chirmoqchi bo'lgan kino kodini kiriting:",
        reply_markup=cancel_reply_keyboard()
    )
    await callback.answer()


@router.message(DeleteMovie.waiting_for_code)
async def delete_movie_code(message: Message, state: FSMContext):
    """Kino kodini olish va o'chirish"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    code = message.text.strip()
    movie = get_movie_by_code(code)
    
    if not movie:
        await message.answer(f"❌ <code>{code}</code> kodli kino topilmadi!", parse_mode="HTML")
        return
    
    success = delete_movie(code)
    
    if success:
        await message.answer(
            f"✅ Kino o'chirildi!\n\n"
            f"🔢 Kod: <code>{code}</code>\n"
            f"🎬 Nomi: {movie['title']}",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=admin_menu_keyboard())
    
    await state.clear()


@router.callback_query(F.data == "movie_search")
async def movie_search_handler(callback: CallbackQuery, state: FSMContext):
    """Kino qidirish"""
    if not is_admin(callback.from_user.id):
        return
    
    from states import SearchMovie
    await state.set_state(SearchMovie.waiting_for_query)
    await callback.message.answer(
        "🔍 Kino nomini yoki kodini kiriting:",
        reply_markup=cancel_reply_keyboard()
    )
    await callback.answer()


# ===== KANAL BOSHQARUVI =====

@router.callback_query(F.data == "admin_channels")
async def admin_channels_handler(callback: CallbackQuery):
    """Kanal boshqaruvi"""
    if not is_admin(callback.from_user.id):
        return
    
    sub_enabled = is_subscription_enabled()
    channels_count = get_channels_count()
    channels = get_all_channels()
    
    status = "Yoqilgan ✅" if sub_enabled else "O'chirilgan ❌"
    
    text = f"""
📺 <b>Kanal boshqaruvi</b>

🔔 Majburiy obuna: <b>{status}</b>

"""
    
    if channels:
        text += "<b>Kanallar ro'yxati:</b>\n"
        for ch in channels:
            text += f"+ {ch['title']} (<code>{ch['channel_id']}</code>)\n"
    else:
        text += "Hech qanday majburiy obuna kanali yo'q.\n"
    
    text += "\n<i>Amalni tanlang:</i>"
    
    await callback.message.edit_text(
        text,
        reply_markup=channel_management_keyboard(sub_enabled, channels_count),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "channel_toggle_sub")
async def toggle_subscription_handler(callback: CallbackQuery):
    """Majburiy obunani yoqish/o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    
    new_status = toggle_subscription()
    status_text = "yoqildi ?" if new_status else "o'chirildi ?"
    
    await callback.answer(f"Majburiy obuna {status_text}", show_alert=True)
    
    # Panelni yangilash
    await admin_channels_handler(callback)


@router.callback_query(F.data == "channel_add")
async def channel_add_handler(callback: CallbackQuery, state: FSMContext):
    """Kanal qo'shish"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.set_state(AddChannel.waiting_for_channel)
    await callback.message.answer(
        "📺 Kanal qo'shish uchun:\n\n"
        "1️⃣ Botni kanalga admin qiling\n"
        "2️⃣ Kanaldan xabarni forward qiling yoki kanal ID ni yuboring\n\n"
        "Masalan: <code>-1001234567890</code>",
        reply_markup=cancel_reply_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddChannel.waiting_for_channel, F.forward_from_chat)
async def add_channel_forward(message: Message, state: FSMContext):
    """Forward qilingan xabardan kanal qo'shish"""
    chat = message.forward_from_chat
    
    if chat.type not in ['channel']:
        await message.answer("⚠️ Faqat kanaldan forward qiling!")
        return
    
    success = add_channel(
        channel_id=chat.id,
        channel_username=chat.username,
        title=chat.title
    )
    
    if success:
        await message.answer(
            f"✅ Kanal qo'shildi!\n\n"
            f"🎬 Nomi: {chat.title}\n"
            f"🆔 ID: <code>{chat.id}</code>",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "⚠️ Bu kanal allaqachon qo'shilgan!",
            reply_markup=admin_menu_keyboard()
        )
    
    await state.clear()


@router.message(AddChannel.waiting_for_channel)
async def add_channel_id(message: Message, state: FSMContext):
    """ID orqali kanal qo'shish"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    try:
        channel_id = int(message.text.strip())
        
        # Kanal ma'lumotlarini olishga urinish
        try:
            chat = await message.bot.get_chat(channel_id)
            title = chat.title
            username = chat.username
        except:
            title = f"Kanal {channel_id}"
            username = None
        
        success = add_channel(
            channel_id=channel_id,
            channel_username=username,
            title=title
        )
        
        if success:
            await message.answer(
                f"✅ Kanal qo'shildi!\n\n"
                f"🎬 Nomi: {title}\n"
                f"🆔 ID: <code>{channel_id}</code>",
                reply_markup=admin_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "⚠️ Bu kanal allaqachon qo'shilgan!",
                reply_markup=admin_menu_keyboard()
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri format!\n"
            "Kanal ID raqam bo'lishi kerak.\n\n"
            "Masalan: <code>-1001234567890</code>",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "channel_delete")
async def channel_delete_handler(callback: CallbackQuery, state: FSMContext):
    """Kanal o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    
    channels = get_all_channels()
    
    if not channels:
        await callback.answer("�� Kanallar ro'yxati bo'sh!", show_alert=True)
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    buttons = []
    for ch in channels:
        # Turi bo'yicha emoji
        if ch.get('is_request_group'):
            type_emoji = "📺"
        elif ch.get('invite_link') and not ch.get('is_request_group'):
            type_emoji = "📺"
        else:
            type_emoji = "📺"
        
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {type_emoji} {ch['title']}",
                callback_data=f"delete_channel_{ch['channel_id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_channels")])
    
    await callback.message.edit_text(
        "🗑 O'chirmoqchi bo'lgan kanalni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_channel_"))
async def delete_channel_confirm(callback: CallbackQuery):
    """Kanalni o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    
    channel_id = int(callback.data.split("_")[-1])
    success = delete_channel(channel_id)
    
    if success:
        await callback.answer("✅ Kanal o'chirildi!", show_alert=True)
    else:
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)
    
    await admin_channels_handler(callback)


@router.callback_query(F.data == "channels_list")
async def channels_list_handler(callback: CallbackQuery):
    """Kanallar ro'yxati"""
    if not is_admin(callback.from_user.id):
        return
    
    channels = get_all_channels()
    
    if not channels:
        await callback.answer("�� Kanallar ro'yxati bo'sh!", show_alert=True)
        return
    
    text = "📺 <b>Kanallar ro'yxati:</b>\n\n"
    for i, ch in enumerate(channels, 1):
        # Turi bo'yicha emoji
        if ch.get('is_request_group'):
            type_emoji = "📺"
            type_name = "So'rovli"
        elif ch.get('invite_link'):
            type_emoji = "📺"
            type_name = "Havola"
        else:
            type_emoji = "📺"
            type_name = "Kanal"
        
        text += f"{i}. {type_emoji} {ch['title']}\n"
        text += f"   📌 Turi: {type_name}\n"
        text += f"   🆔 <code>{ch['channel_id']}</code>\n"
        if ch.get('invite_link'):
            text += f"   🆔 {ch['invite_link']}\n"
        elif ch.get('url'):
            text += f"   🆔 {ch['url']}\n"
        text += "\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard("admin_channels"),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(SetBaseChannel.waiting_for_channel, F.chat_shared)
async def set_base_channel_from_request(message: Message, state: FSMContext):
    """Tanlangan kanaldan baza kanalni sozlash"""
    chat_shared = message.chat_shared
    channel_id = chat_shared.chat_id
    
    # Kanal ma'lumotlarini olish
    try:
        chat = await message.bot.get_chat(channel_id)
        title = chat.title
        
        # Botning admin ekanligini tekshirish
        bot_member = await message.bot.get_chat_member(channel_id, message.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.answer(
                "⚠️ Bot bu kanalda admin emas!\n\n"
                "Botni kanalga admin qilib qo'shing va qaytadan urinib ko'ring.",
                reply_markup=admin_menu_keyboard()
            )
            await state.clear()
            return
            
    except Exception as e:
        title = f"Kanal"
        
    set_base_channel(str(channel_id))
    
    await message.answer(
        f"? Baza kanal muvaffaqiyatli sozlandi!\n\n"
        f"📺 Kanal: <b>{title}</b>\n"
        f"🆔 ID: <code>{channel_id}</code>\n\n"
        f"Endi kinolar shu kanalga yuklanadi.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )
    await state.clear()


@router.message(SetBaseChannel.waiting_for_channel)
async def set_base_channel_handler(message: Message, state: FSMContext):
    """Baza kanalni saqlash (matn orqali)"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    # Agar raqam yuborilsa
    try:
        channel_id = int(message.text.strip())
        
        # Kanal mavjudligini tekshirish
        try:
            chat = await message.bot.get_chat(channel_id)
            title = chat.title
        except:
            await message.answer(
                "⚠️ Kanal topilmadi yoki bot admin emas!\n"
                "Qaytadan urinib ko'ring.",
                reply_markup=select_base_channel_keyboard()
            )
            return
        
        set_base_channel(str(channel_id))
        
        await message.answer(
            f"? Baza kanal sozlandi!\n\n"
            f"📺 Kanal: <b>{title}</b>\n"
            f"🆔 ID: <code>{channel_id}</code>",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri format!\n"
            "Tugmani bosib kanal tanlang yoki kanal ID raqamini yuboring.",
            reply_markup=select_base_channel_keyboard()
        )


# ===== XABAR YUBORISH (REKLAMA) - KENGAYTIRILGAN =====

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_handler(callback: CallbackQuery, state: FSMContext):
    """Xabar yuborishni boshlash"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.clear()
    users_count = get_users_count()
    
    from keyboards import broadcast_type_keyboard
    await callback.message.edit_text(
        f"📢 <b>Xabar yuborish</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{users_count}</b>\n\n"
        "📝 Xabar turini tanlang:",
        reply_markup=broadcast_type_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# Oddiy matn xabari
@router.callback_query(F.data == "broadcast_text")
async def broadcast_text_handler(callback: CallbackQuery, state: FSMContext):
    """Oddiy matn xabari"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.update_data(broadcast_type="text", buttons=[])
    await state.set_state(Broadcast.waiting_for_message)
    
    await callback.message.edit_text(
        "📝 <b>Oddiy matn xabari</b>\n\n"
        "Xabar matnini yuboring:",
        parse_mode="HTML"
    )
    await callback.answer()


# Matn + Tugma
@router.callback_query(F.data == "broadcast_text_button")
async def broadcast_text_button_handler(callback: CallbackQuery, state: FSMContext):
    """Matn + tugma xabari"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.update_data(broadcast_type="text_button", buttons=[])
    await state.set_state(Broadcast.waiting_for_message)
    
    await callback.message.edit_text(
        "? <b>Matn + Tugma xabari</b>\n\n"
        "Avval xabar matnini yuboring:",
        parse_mode="HTML"
    )
    await callback.answer()


# Rasm + Matn
@router.callback_query(F.data == "broadcast_photo")
async def broadcast_photo_handler(callback: CallbackQuery, state: FSMContext):
    """Rasm + matn xabari"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.update_data(broadcast_type="photo", buttons=[])
    await state.set_state(Broadcast.waiting_for_media)
    
    from keyboards import broadcast_skip_caption_keyboard
    await callback.message.edit_text(
        "🖼 <b>Rasm + Matn xabari</b>\n\n"
        "Rasmni yuboring:",
        parse_mode="HTML"
    )
    await callback.answer()


# Rasm + Matn + Tugma
@router.callback_query(F.data == "broadcast_photo_button")
async def broadcast_photo_button_handler(callback: CallbackQuery, state: FSMContext):
    """Rasm + matn + tugma xabari"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.update_data(broadcast_type="photo_button", buttons=[])
    await state.set_state(Broadcast.waiting_for_media)
    
    await callback.message.edit_text(
        "? <b>Rasm + Matn + Tugma xabari</b>\n\n"
        "Rasmni yuboring:",
        parse_mode="HTML"
    )
    await callback.answer()


# Video + Matn
@router.callback_query(F.data == "broadcast_video")
async def broadcast_video_handler(callback: CallbackQuery, state: FSMContext):
    """Video + matn xabari"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.update_data(broadcast_type="video", buttons=[])
    await state.set_state(Broadcast.waiting_for_media)
    
    await callback.message.edit_text(
        "📹 <b>Video + Matn xabari</b>\n\n"
        "Videoni yuboring:",
        parse_mode="HTML"
    )
    await callback.answer()


# Video + Matn + Tugma
@router.callback_query(F.data == "broadcast_video_button")
async def broadcast_video_button_handler(callback: CallbackQuery, state: FSMContext):
    """Video + matn + tugma xabari"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.update_data(broadcast_type="video_button", buttons=[])
    await state.set_state(Broadcast.waiting_for_media)
    
    await callback.message.edit_text(
        "📹 <b>Video + Matn + Tugma xabari</b>\n\n"
        "Videoni yuboring:",
        parse_mode="HTML"
    )
    await callback.answer()


# Forward qilish
@router.callback_query(F.data == "broadcast_forward")
async def broadcast_forward_handler(callback: CallbackQuery, state: FSMContext):
    """Forward qilish"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.update_data(broadcast_type="forward", buttons=[])
    await state.set_state(Broadcast.waiting_for_message)
    
    await callback.message.edit_text(
        "↩️ <b>Forward qilish</b>\n\n"
        "Xabarni forward qiling yoki yuboring:",
        parse_mode="HTML"
    )
    await callback.answer()


# Matn qabul qilish
@router.message(Broadcast.waiting_for_message)
async def broadcast_receive_message(message: Message, state: FSMContext):
    """Matn xabarini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    data = await state.get_data()
    broadcast_type = data.get("broadcast_type", "text")
    
    if broadcast_type == "forward":
        # Forward qilish
        await state.update_data(forward_message_id=message.message_id, forward_chat_id=message.chat.id)
        from keyboards import broadcast_confirm_keyboard
        await message.answer(
            "? Xabar tayyor!\n\n"
            "Yuborishni tasdiqlang:",
            reply_markup=broadcast_confirm_keyboard()
        )
        await state.set_state(Broadcast.confirm)
        return
    
    await state.update_data(message_text=message.text, message_entities=message.entities)
    
    if broadcast_type == "text":
        # Oddiy matn - tasdiqlash
        from keyboards import broadcast_confirm_keyboard
        await message.answer(
            "? Xabar tayyor!\n\n"
            f"👁 <b>Ko'rinishi:</b>\n{message.text}\n\n"
            "Yuborishni tasdiqlang:",
            reply_markup=broadcast_confirm_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(Broadcast.confirm)
    elif broadcast_type == "text_button":
        # Matn + tugma - tugma so'rash
        await message.answer(
            "🔘 <b>Tugma qo'shish</b>\n\n"
            "Tugma matnini kiriting:\n"
            "<i>(Masalan: 📢 Kanalga o'tish)</i>",
            parse_mode="HTML"
        )
        await state.set_state(Broadcast.waiting_for_button_text)


# Rasm/Video qabul qilish
@router.message(Broadcast.waiting_for_media, F.photo | F.video)
async def broadcast_receive_media(message: Message, state: FSMContext):
    """Rasm yoki video qabul qilish"""
    data = await state.get_data()
    broadcast_type = data.get("broadcast_type", "photo")
    
    if message.photo:
        await state.update_data(media_type="photo", media_file_id=message.photo[-1].file_id)
    elif message.video:
        await state.update_data(media_type="video", media_file_id=message.video.file_id)
    
    from keyboards import broadcast_skip_caption_keyboard
    await message.answer(
        "📝 Endi xabar matnini yuboring:\n\n"
        "<i>Yoki matnsiz yuborish uchun tugmani bosing:</i>",
        reply_markup=broadcast_skip_caption_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Broadcast.waiting_for_caption)


# Caption qabul qilish
@router.message(Broadcast.waiting_for_caption)
async def broadcast_receive_caption(message: Message, state: FSMContext):
    """Caption qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    data = await state.get_data()
    broadcast_type = data.get("broadcast_type", "photo")
    
    await state.update_data(message_text=message.text, message_entities=message.entities)
    
    if "button" in broadcast_type:
        # Tugma qo'shish kerak
        await message.answer(
            "🔘 <b>Tugma qo'shish</b>\n\n"
            "Tugma matnini kiriting:\n"
            "<i>(Masalan: 📢 Kanalga o'tish)</i>",
            parse_mode="HTML"
        )
        await state.set_state(Broadcast.waiting_for_button_text)
    else:
        # Tasdiqlash
        from keyboards import broadcast_confirm_keyboard
        await message.answer(
            "? Xabar tayyor!\n\nYuborishni tasdiqlang:",
            reply_markup=broadcast_confirm_keyboard()
        )
        await state.set_state(Broadcast.confirm)


# Caption o'tkazish
@router.callback_query(F.data == "broadcast_skip_caption")
async def broadcast_skip_caption(callback: CallbackQuery, state: FSMContext):
    """Captionsiz davom etish"""
    if not is_admin(callback.from_user.id):
        return
    
    data = await state.get_data()
    broadcast_type = data.get("broadcast_type", "photo")
    
    await state.update_data(message_text=None, message_entities=None)
    
    if "button" in broadcast_type:
        await callback.message.edit_text(
            "🔘 <b>Tugma qo'shish</b>\n\n"
            "Tugma matnini kiriting:\n"
            "<i>(Masalan: 📢 Kanalga o'tish)</i>",
            parse_mode="HTML"
        )
        await state.set_state(Broadcast.waiting_for_button_text)
    else:
        from keyboards import broadcast_confirm_keyboard
        await callback.message.edit_text(
            "? Xabar tayyor!\n\nYuborishni tasdiqlang:",
            reply_markup=broadcast_confirm_keyboard()
        )
        await state.set_state(Broadcast.confirm)
    await callback.answer()


# Tugma matni
@router.message(Broadcast.waiting_for_button_text)
async def broadcast_receive_button_text(message: Message, state: FSMContext):
    """Tugma matnini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    await state.update_data(current_button_text=message.text)
    
    await message.answer(
        f"🔗 <b>Tugma havolasi</b>\n\n"
        f"Tugma: <code>{message.text}</code>\n\n"
        "Havola kiriting:\n"
        "<i>(Masalan: https://t.me/kanal)</i>",
        parse_mode="HTML"
    )
    await state.set_state(Broadcast.waiting_for_button_url)


# Tugma havolasi
@router.message(Broadcast.waiting_for_button_url)
async def broadcast_receive_button_url(message: Message, state: FSMContext):
    """Tugma havolasini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    url = message.text.strip()
    
    # URL tekshirish
    if not url.startswith(("http://", "https://", "tg://")):
        await message.answer("? Noto'g'ri havola formati!\n\nQaytadan kiriting:")
        return
    
    data = await state.get_data()
    buttons = data.get("buttons", [])
    button_text = data.get("current_button_text", "Tugma")
    
    buttons.append({"text": button_text, "url": url})
    await state.update_data(buttons=buttons)
    
    from keyboards import broadcast_button_keyboard
    
    buttons_text = "\n".join([f"🔘 {b['text']} - {b['url']}" for b in buttons])
    
    await message.answer(
        f"? Tugma qo'shildi!\n\n"
        f"<b>Tugmalar:</b>\n{buttons_text}\n\n"
        "Yana tugma qo'shish yoki yuborishni tasdiqlash:",
        reply_markup=broadcast_button_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(Broadcast.confirm)


# Yana tugma qo'shish
@router.callback_query(F.data == "broadcast_add_more_button")
async def broadcast_add_more_button(callback: CallbackQuery, state: FSMContext):
    """Yana tugma qo'shish"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        "🔘 <b>Yana tugma qo'shish</b>\n\n"
        "Tugma matnini kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(Broadcast.waiting_for_button_text)
    await callback.answer()


# Tugma qo'shish (confirm holida)
@router.callback_query(F.data == "broadcast_add_button")
async def broadcast_add_button(callback: CallbackQuery, state: FSMContext):
    """Tugma qo'shish"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text(
        "🔘 <b>Tugma qo'shish</b>\n\n"
        "Tugma matnini kiriting:\n"
        "<i>(Masalan: 📢 Kanalga o'tish)</i>",
        parse_mode="HTML"
    )
    await state.set_state(Broadcast.waiting_for_button_text)
    await callback.answer()


# Xabar yuborish
@router.callback_query(F.data == "broadcast_send")
async def broadcast_send(callback: CallbackQuery, state: FSMContext):
    """Xabarni yuborish"""
    if not is_admin(callback.from_user.id):
        return
    
    data = await state.get_data()
    broadcast_type = data.get("broadcast_type", "text")
    buttons = data.get("buttons", [])
    
    # Inline tugmalarni yaratish
    inline_keyboard = None
    if buttons:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard_buttons = []
        for btn in buttons:
            keyboard_buttons.append([InlineKeyboardButton(text=btn["text"], url=btn["url"])])
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    users = get_all_users()
    success = 0
    failed = 0
    
    await callback.message.edit_text(f"📤 Xabar {len(users)} foydalanuvchiga yuborilmoqda...")
    
    for user_id in users:
        try:
            if broadcast_type == "forward":
                # Forward qilish
                await callback.bot.forward_message(
                    chat_id=user_id,
                    from_chat_id=data.get("forward_chat_id"),
                    message_id=data.get("forward_message_id")
                )
            elif "photo" in broadcast_type:
                # Rasm
                await callback.bot.send_photo(
                    chat_id=user_id,
                    photo=data.get("media_file_id"),
                    caption=data.get("message_text"),
                    caption_entities=data.get("message_entities"),
                    reply_markup=inline_keyboard
                )
            elif "video" in broadcast_type:
                # Video
                await callback.bot.send_video(
                    chat_id=user_id,
                    video=data.get("media_file_id"),
                    caption=data.get("message_text"),
                    caption_entities=data.get("message_entities"),
                    reply_markup=inline_keyboard
                )
            else:
                # Matn
                await callback.bot.send_message(
                    chat_id=user_id,
                    text=data.get("message_text"),
                    entities=data.get("message_entities"),
                    reply_markup=inline_keyboard
                )
            success += 1
        except Exception as e:
            failed += 1
    
    await state.clear()
    await callback.message.edit_text(
        f"? <b>Xabar yuborildi!</b>\n\n"
        f"✅ Muvaffaqiyatli: <b>{success}</b>\n"
        f"? Xatolik: <b>{failed}</b>",
        parse_mode="HTML"
    )
    await callback.message.answer("📋 Asosiy menyu:", reply_markup=admin_menu_keyboard())


# Bekor qilish
@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Xabar yuborishni bekor qilish"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.clear()
    await callback.message.edit_text("? Xabar yuborish bekor qilindi")
    await callback.message.answer("📋 Asosiy menyu:", reply_markup=admin_menu_keyboard())
    await callback.answer()


# ===== BEKOR QILISH =====

@router.callback_query(F.data == "cancel_action")
async def cancel_action_handler(callback: CallbackQuery, state: FSMContext):
    """Amalni bekor qilish"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Bekor qilindi",
        reply_markup=back_keyboard()
    )
    await callback.answer()


# ===== ADMIN BOSHQARUVI =====

@router.callback_query(F.data == "admin_admins")
async def admin_admins_handler(callback: CallbackQuery):
    """Admin boshqaruvi"""
    if not is_admin(callback.from_user.id):
        return
    
    from config import ADMINS
    from keyboards import admin_management_keyboard
    db_admins = get_all_admins()
    all_admins = list(set(ADMINS + db_admins))
    
    text = f"""
👑 <b>Adminlar boshqaruvi</b>

📊 <b>Statistika:</b>
+ Jami adminlar: <code>{len(all_admins)}</code>
+ Config adminlar: <code>{len(ADMINS)}</code>
L Qo'shilgan adminlar: <code>{len(db_admins)}</code>
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_management_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admins_list")
async def admins_list_handler(callback: CallbackQuery):
    """Adminlar ro'yxati"""
    if not is_admin(callback.from_user.id):
        return
    
    from config import ADMINS
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    db_admins = get_all_admins()
    all_admins = list(set(ADMINS + db_admins))
    
    text = f"👑 <b>Adminlar ro'yxati</b>\n\n"
    text += f"👑 - Config admin (o'chirilmaydi)\n"
    text += f"👤 - Qo'shilgan admin\n\n"
    
    buttons = []
    for admin_id in all_admins:
        is_config = admin_id in ADMINS
        status = "👑" if is_config else "👤"
        
        # Admin haqida ma'lumot olish
        try:
            user_info = await callback.bot.get_chat(admin_id)
            full_name = user_info.full_name
            username = f"@{user_info.username}" if user_info.username else ""
        except:
            full_name = "Noma'lum"
            username = ""
        
        if username:
            button_text = f"{status} {full_name} {username}"
            text += f"{status} {full_name} {username} - <code>{admin_id}</code>\n"
        else:
            button_text = f"{status} {full_name}"
            text += f"{status} {full_name} - <code>{admin_id}</code>\n"
        
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"view_admin_{admin_id}"
            )
        ])
    
    text += f"\n<b>Jami:</b> {len(all_admins)} admin"
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_admins")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view_admin_"))
async def view_admin_handler(callback: CallbackQuery):
    """Admin ma'lumotlarini ko'rish"""
    if not is_admin(callback.from_user.id):
        return
    
    admin_id = int(callback.data.replace("view_admin_", ""))
    
    from config import ADMINS
    from keyboards import admin_view_keyboard
    
    is_config_admin = admin_id in ADMINS
    status = "👑 Config admin" if is_config_admin else "👤 Qo'shilgan admin"
    
    # Admin haqida ma'lumot olish
    try:
        user_info = await callback.bot.get_chat(admin_id)
        full_name = user_info.full_name
        username = f"@{user_info.username}" if user_info.username else "Yo'q"
    except:
        full_name = "Noma'lum"
        username = "Noma'lum"
    
    text = f"""
👤 <b>Admin ma'lumotlari</b>

🆔 ID: <code>{admin_id}</code>
👤 Ism: {full_name}
📝 Username: {username}
📊 Status: {status}
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_view_keyboard(admin_id, is_config_admin),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add")
async def admin_add_handler(callback: CallbackQuery, state: FSMContext):
    """Admin qo'shish"""
    if not is_admin(callback.from_user.id):
        return
    
    from states import AddAdmin
    await state.set_state(AddAdmin.waiting_for_user_id)
    
    await callback.message.edit_text(
        "? <b>Admin qo'shish</b>\n\n"
        "Yangi admin qo'shish usullaridan birini tanlang:\n\n"
        "1️⃣ Admin ID raqamini yuboring\n"
        "<i>Masalan: 123456789</i>\n\n"
        "2️⃣ Yoki foydalanuvchi xabarini forward qiling\n\n"
        "💡 ID ni olish uchun @userinfobot dan foydalanish mumkin",
        parse_mode="HTML"
    )
    await callback.answer()


from states import AddAdmin, RemoveAdmin

@router.message(AddAdmin.waiting_for_user_id)
async def admin_add_receive_id(message: Message, state: FSMContext):
    """Admin ID qabul qilish yoki forward xabar"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    new_admin_id = None
    full_name = None
    
    # Forward xabar tekshirish
    if message.forward_from:
        new_admin_id = message.forward_from.id
        full_name = message.forward_from.full_name
    elif message.forward_sender_name:
        await message.answer(
            "? Bu foydalanuvchi maxfiylik sozlamalari tufayli ID sini yashirgan.\n\n"
            "Iltimos, ID raqamini to'g'ridan-to'g'ri yuboring:"
        )
        return
    elif message.text:
        try:
            new_admin_id = int(message.text.strip())
        except ValueError:
            await message.answer("? Noto'g'ri format! ID raqam yoki forward xabar yuboring:")
            return
    else:
        await message.answer("? ID raqam yoki forward xabar yuboring:")
        return
    
    from config import ADMINS
    from database import add_admin
    
    # Allaqachon admin ekanligini tekshirish
    if new_admin_id in ADMINS or new_admin_id in get_all_admins():
        await message.answer("? Bu foydalanuvchi allaqachon admin!")
        await state.clear()
        return
    
    # Agar forward dan olgan bo'lsak, ism bor. Aks holda olishga harakat qilamiz
    if not full_name:
        try:
            user_info = await message.bot.get_chat(new_admin_id)
            full_name = user_info.full_name
        except:
            full_name = "Noma'lum"
    
    success = add_admin(new_admin_id, full_name)
    
    if success:
        await message.answer(
            f"? <b>Admin qo'shildi!</b>\n\n"
            f"🆔 ID: <code>{new_admin_id}</code>\n"
            f"👤 Ism: {full_name}\n\n"
            f"⚙️ Huquqlarni boshqarish uchun adminlar ro'yxatidan tanlang.",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
        
        # Yangi adminga xabar yuborish
        try:
            await message.bot.send_message(
                new_admin_id,
                "🎉 <b>Tabriklaymiz!</b>\n\n"
                "Siz admin sifatida tayinlandingiz!\n"
                "Admin paneliga kirish uchun /start buyrug'ini yuboring.",
                parse_mode="HTML"
            )
        except:
            pass
    else:
        await message.answer(
            "❌ Xatolik yuz berdi!",
            reply_markup=admin_menu_keyboard()
        )
    
    await state.clear()


@router.callback_query(F.data == "admin_remove")
async def admin_remove_handler(callback: CallbackQuery, state: FSMContext):
    """Admin o'chirish - ro'yxat ko'rsatish"""
    if not is_admin(callback.from_user.id):
        return
    
    from config import ADMINS
    db_admins = get_all_admins()
    
    # Faqat o'chiriladigan adminlar (config adminlarni olib tashlash)
    removable_admins = [admin_id for admin_id in db_admins if admin_id not in ADMINS]
    
    if not removable_admins:
        await callback.answer("? O'chiriladigan admin yo'q!", show_alert=True)
        return
    
    # Adminlar ro'yxati tugmalari
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    
    text = "🗑 <b>Admin o'chirish</b>\n\n"
    text += "O'chirmoqchi bo'lgan adminni tanlang:\n\n"
    
    for admin_id in removable_admins:
        try:
            user_info = await callback.bot.get_chat(admin_id)
            full_name = user_info.full_name
            username = f"@{user_info.username}" if user_info.username else ""
        except:
            full_name = "Noma'lum"
            username = ""
        
        if username:
            button_text = f"👤 {full_name} {username}"
            text += f"👤 {full_name} {username} - <code>{admin_id}</code>\n"
        else:
            button_text = f"👤 {full_name}"
            text += f"�� {full_name} - <code>{admin_id}</code>\n"
        
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"confirm_remove_admin_{admin_id}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_admins")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.message(RemoveAdmin.waiting_for_user_id)
async def admin_remove_receive_id(message: Message, state: FSMContext):
    """O'chiriladigan admin ID"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    try:
        admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("? Noto'g'ri format! Faqat raqam kiriting:")
        return
    
    from config import ADMINS
    
    if admin_id in ADMINS:
        await message.answer("? Config adminni o'chirib bo'lmaydi!")
        await state.clear()
        return
    
    if admin_id not in get_all_admins():
        await message.answer("? Bu foydalanuvchi admin emas!")
        await state.clear()
        return
    
    from database import remove_admin
    success = remove_admin(admin_id)
    
    if success:
        await message.answer(
            f"? Admin o'chirildi!\n\n🆔 ID: <code>{admin_id}</code>",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
        
        # O'chirilgan adminga xabar
        try:
            await message.bot.send_message(
                admin_id,
                "❌ Sizning admin huquqlaringiz olib tashlandi."
            )
        except:
            pass
    else:
        await message.answer("❌ Xatolik yuz berdi!", reply_markup=admin_menu_keyboard())
    
    await state.clear()


@router.callback_query(F.data.startswith("confirm_remove_admin_"))
async def confirm_remove_admin_handler(callback: CallbackQuery):
    """Adminni o'chirishni tasdiqlash"""
    if not is_admin(callback.from_user.id):
        return
    
    admin_id = int(callback.data.replace("confirm_remove_admin_", ""))
    
    # Admin haqida ma'lumot olish
    try:
        user_info = await callback.bot.get_chat(admin_id)
        full_name = user_info.full_name
        username = f"@{user_info.username}" if user_info.username else ""
    except:
        full_name = "Noma'lum"
        username = ""
    
    admin_info = f"{full_name} {username}".strip() if username else full_name
    
    from keyboards import confirm_remove_admin_keyboard
    await callback.message.edit_text(
        f"⚠️ <b>Tasdiqlash</b>\n\n"
        f"👤 Admin: {admin_info}\n"
        f"🆔 ID: <code>{admin_id}</code>\n\n"
        f"Adminni o'chirmoqchimisiz?",
        reply_markup=confirm_remove_admin_keyboard(admin_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("remove_admin_"))
async def remove_admin_handler(callback: CallbackQuery):
    """Adminni o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    
    admin_id = int(callback.data.replace("remove_admin_", ""))
    
    from config import ADMINS
    if admin_id in ADMINS:
        await callback.answer("? Config adminni o'chirib bo'lmaydi!", show_alert=True)
        return
    
    # Admin haqida ma'lumot olish (o'chirishdan oldin)
    try:
        user_info = await callback.bot.get_chat(admin_id)
        full_name = user_info.full_name
        username = f"@{user_info.username}" if user_info.username else ""
    except:
        full_name = "Noma'lum"
        username = ""
    
    admin_info = f"{full_name} {username}".strip() if username else full_name
    
    from database import remove_admin
    success = remove_admin(admin_id)
    
    if success:
        await callback.answer("? Admin o'chirildi!", show_alert=True)
        
        # O'chirilgan adminga xabar
        try:
            await callback.bot.send_message(
                admin_id,
                "❌ Sizning admin huquqlaringiz olib tashlandi."
            )
        except:
            pass
        
        # Ro'yxatga qaytish
        from keyboards import admin_management_keyboard
        db_admins = get_all_admins()
        all_admins = list(set(ADMINS + db_admins))
        
        text = f"""
👑 <b>Adminlar boshqaruvi</b>

? <b>Admin o'chirildi!</b>
👤 {admin_info}
🆔 ID: <code>{admin_id}</code>

📊 <b>Statistika:</b>
+ Jami adminlar: <code>{len(all_admins)}</code>
+ Config adminlar: <code>{len(ADMINS)}</code>
L Qo'shilgan adminlar: <code>{len(db_admins)}</code>
"""
        await callback.message.edit_text(
            text,
            reply_markup=admin_management_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)


@router.callback_query(F.data == "admin_permissions")
async def admin_permissions_handler(callback: CallbackQuery):
    """Huquqlar bo'limi - umumiy ma'lumot"""
    if not is_admin(callback.from_user.id):
        return
    
    text = """
👑 <b>Admin huquqlari tizimi</b>

<b>Super Admin (Config admin):</b>
✅ Barcha huquqlarga ega
🔒 O'chirilmaydi
👑 Boshqa adminlarni boshqaradi

<b>Oddiy Admin:</b>
✅ Super admin bergan huquqlarga ega
⚠️ Huquqlari cheklanishi mumkin

<b>Huquqlar turlari:</b>
🎬 Kino boshqaruvi
�� Kanal boshqaruvi
📤 Xabar yuborish
📊 Statistika
💎 Premium boshqaruvi
👑 Admin boshqaruvi
⚙️ Bot sozlamalari

⚙️ Huquqlarni boshqarish uchun adminlar ro'yxatidan admini tanlang.
"""
    
    from keyboards import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👑 Adminlar ro'yxati", callback_data="admins_list")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_admins")]
        ]
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_perms_"))
async def edit_admin_permissions_handler(callback: CallbackQuery):
    """Admin huquqlarini tahrirlash"""
    if not is_admin(callback.from_user.id):
        return
    
    admin_id = int(callback.data.replace("edit_perms_", ""))
    
    from database import get_admin_permissions
    from keyboards import admin_permissions_keyboard
    
    perms = get_admin_permissions(admin_id)
    if not perms:
        await callback.answer("? Admin topilmadi!", show_alert=True)
        return
    
    try:
        user_info = await callback.bot.get_chat(admin_id)
        full_name = user_info.full_name
    except:
        full_name = "Noma'lum"
    
    text = f"""
⚙️ <b>Huquqlarni boshqarish</b>

👤 Admin: {full_name}
🆔 ID: <code>{admin_id}</code>

Huquqni yoqish/o'chirish uchun tugmani bosing:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_permissions_keyboard(admin_id, perms),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_perm_"))
async def toggle_permission_handler(callback: CallbackQuery):
    """Huquqni yoqish/o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    
    # Format: toggle_perm_123456789_can_movies
    parts = callback.data.split("_")
    admin_id = int(parts[2])
    permission = "_".join(parts[3:])  # can_movies, can_channels, etc.
    
    from database import get_admin_permissions, update_admin_permission
    from keyboards import admin_permissions_keyboard
    
    # Joriy holatni olish
    perms = get_admin_permissions(admin_id)
    if not perms:
        await callback.answer("? Admin topilmadi!", show_alert=True)
        return
    
    # Holatni o'zgartirish
    current_value = perms.get(permission, False)
    new_value = not current_value
    
    success = update_admin_permission(admin_id, permission, new_value)
    
    if success:
        status = "yoqildi ?" if new_value else "o'chirildi ?"
        await callback.answer(f"Huquq {status}", show_alert=False)
        
        # Yangilangan huquqlarni olish va klaviaturani yangilash
        perms = get_admin_permissions(admin_id)
        
        try:
            user_info = await callback.bot.get_chat(admin_id)
            full_name = user_info.full_name
        except:
            full_name = "Noma'lum"
        
        text = f"""
⚙️ <b>Huquqlarni boshqarish</b>

? Admin: {full_name}
🆔 ID: <code>{admin_id}</code>

Huquqni yoqish/o'chirish uchun tugmani bosing:
"""
        
        await callback.message.edit_text(
            text,
            reply_markup=admin_permissions_keyboard(admin_id, perms),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)


@router.callback_query(F.data == "permissions_info")
async def permissions_info_handler(callback: CallbackQuery):
    """Huquqlar haqida batafsil"""
    if not is_admin(callback.from_user.id):
        return
    
    text = """
ℹ️ <b>Huquqlar haqida batafsil</b>

<b>🎬 Kino boshqaruvi:</b>
Kino qo'shish, o'chirish, tahrirlash

<b>�� Kanal boshqaruvi:</b>
Majburiy obuna kanallarini boshqarish

<b>📤 Xabar yuborish:</b>
Barcha foydalanuvchilarga xabar yuborish

<b>📊 Statistika:</b>
Bot statistikasini ko'rish

<b>💎 Premium boshqaruvi:</b>
Premium tariflar va to'lovlarni boshqarish

<b>👑 Admin boshqaruvi:</b>
Adminlarni qo'shish/o'chirish (Super admin)

<b>⚙️ Bot sozlamalari:</b>
Bot konfiguratsiyasini o'zgartirish
"""
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_permissions")]
        ]
    )
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_referral")
async def admin_referral_handler(callback: CallbackQuery):
    """Referal bo'limi - inline"""
    if not is_admin(callback.from_user.id):
        return
    
    from database import (
        is_referral_enabled, get_referral_bonus, get_min_withdrawal,
        get_total_referral_stats
    )
    from keyboards import referral_admin_keyboard
    
    is_enabled = is_referral_enabled()
    bonus = get_referral_bonus()
    min_withdrawal = get_min_withdrawal()
    stats = get_total_referral_stats()
    
    status = "🟢 Yoniq" if is_enabled else "🔴 O'chiq"
    
    text = f"""
🔗 <b>Referal boshqaruvi</b>

📊 <b>Holat:</b> {status}

⚙️ <b>Sozlamalar:</b>
+ Har bir referal: <b>{bonus:,} so'm</b>
L Min. chiqarish: <b>{min_withdrawal:,} so'm</b>

📊 <b>Statistika:</b>
+ Jami referallar: <b>{stats['total_referrals']}</b>
+ Berilgan bonuslar: <b>{stats['total_bonuses']:,} so'm</b>
+ Chiqarilgan pul: <b>{stats['total_withdrawn']:,} so'm</b>
L Kutilayotgan so'rovlar: <b>{stats['pending_requests']}</b>
"""
    
    await callback.message.edit_text(text, reply_markup=referral_admin_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "referral_stats")
async def referral_stats_handler(callback: CallbackQuery):
    """Referal statistikasi"""
    if not is_admin(callback.from_user.id):
        return
    
    from database import get_total_referral_stats
    stats = get_total_referral_stats()
    
    text = f"""
📊 <b>Referal statistikasi</b>

👥 <b>Jami referallar:</b> {stats['total_referrals']}
💰 <b>Berilgan bonuslar:</b> {stats['total_bonuses']:,} so'm
💵 <b>Chiqarilgan pul:</b> {stats['total_withdrawn']:,} so'm
? <b>Kutilayotgan so'rovlar:</b> {stats['pending_requests']}
"""
    
    if stats['top_referrers']:
        text += "\n🏆 <b>Top referralchilar:</b>\n"
        for i, ref in enumerate(stats['top_referrers'][:5], 1):
            name = ref['full_name'] if ref['full_name'] else f"ID: {ref['user_id']}"
            text += f"{i}. {name} - {ref['ref_count']} ta\n"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_referral")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "referral_settings")
async def referral_settings_handler(callback: CallbackQuery):
    """Referal sozlamalari"""
    if not is_admin(callback.from_user.id):
        return
    
    from database import is_referral_enabled, get_referral_bonus, get_min_withdrawal
    from keyboards import referral_settings_keyboard
    
    is_enabled = is_referral_enabled()
    bonus = get_referral_bonus()
    min_withdrawal = get_min_withdrawal()
    
    status = "🟢 Yoniq" if is_enabled else "🔴 O'chiq"
    
    text = f"""
⚙️ <b>Referal sozlamalari</b>

📊 <b>Holat:</b> {status}

⚙️ <b>Sozlamalar:</b>
+ Har bir referal uchun bonus: <b>{bonus:,} so'm</b>
L Minimal pul chiqarish: <b>{min_withdrawal:,} so'm</b>
"""
    
    await callback.message.edit_text(text, reply_markup=referral_settings_keyboard(is_enabled), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "referral_toggle")
async def referral_toggle_handler(callback: CallbackQuery):
    """Referal tizimini yoqish/o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    
    from database import is_referral_enabled, set_referral_enabled
    
    current = is_referral_enabled()
    set_referral_enabled(not current)
    
    new_status = "✅ yoqildi" if not current else "❌ o'chirildi"
    await callback.answer(f"Referal tizimi {new_status}!", show_alert=True)
    
    # Sahifani yangilash
    await referral_settings_handler(callback)


@router.callback_query(F.data == "referral_set_bonus")
async def referral_set_bonus_handler(callback: CallbackQuery, state: FSMContext):
    """Referal bonus summasini o'zgartirish"""
    if not is_admin(callback.from_user.id):
        return
    
    from states import SetReferralBonus
    from database import get_referral_bonus
    
    current = get_referral_bonus()
    
    await state.set_state(SetReferralBonus.waiting_for_amount)
    await callback.message.edit_text(
        f"? <b>Referal bonus summasini kiriting</b>\n\n"
        f"Hozirgi: <b>{current:,} so'm</b>\n\n"
        f"Yangi summani kiriting (faqat raqam):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(SetReferralBonus.waiting_for_amount, F.text.regexp(r'^\d+$'))
async def set_referral_bonus_amount(message: Message, state: FSMContext):
    """Bonus summasini saqlash"""
    if not is_admin(message.from_user.id):
        return
    
    amount = int(message.text)
    
    from database import set_referral_bonus
    set_referral_bonus(amount)
    
    await state.clear()
    await message.answer(
        f"? Referal bonus summasi o'zgartirildi!\n\n"
        f"Yangi summa: <b>{amount:,} so'm</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


@router.message(SetMinWithdrawal.waiting_for_amount, F.text.regexp(r'^\d+$'))
async def set_min_withdrawal_amount(message: Message, state: FSMContext):
    """Minimal pul chiqarish summasini saqlash"""
    if not is_admin(message.from_user.id):
        return
    
    amount = int(message.text)
    
    from database import set_min_withdrawal
    set_min_withdrawal(amount)
    
    await state.clear()
    await message.answer(
        f"? Minimal pul chiqarish summasi o'zgartirildi!\n\n"
        f"Yangi summa: <b>{amount:,} so'm</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "referral_set_min")
async def referral_set_min_handler(callback: CallbackQuery, state: FSMContext):
    """Minimal pul chiqarish summasini o'zgartirish"""
    if not is_admin(callback.from_user.id):
        return
    
    from states import SetMinWithdrawal
    from database import get_min_withdrawal
    
    current = get_min_withdrawal()
    
    await state.set_state(SetMinWithdrawal.waiting_for_amount)
    await callback.message.edit_text(
        f"💵 <b>Minimal pul chiqarish summasini kiriting</b>\n\n"
        f"Hozirgi: <b>{current:,} so'm</b>\n\n"
        f"Yangi summani kiriting (faqat raqam):",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "referral_requests")
async def referral_requests_handler(callback: CallbackQuery):
    """Pul chiqarish so'rovlari"""
    if not is_admin(callback.from_user.id):
        return
    
    from database import get_pending_withdrawals
    from keyboards import withdrawal_requests_keyboard
    
    requests = get_pending_withdrawals()
    
    if not requests:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_referral")]
            ]
        )
        await callback.message.edit_text(
            "💵 <b>Pul chiqarish so'rovlari</b>\n\n"
            "? Hozircha kutilayotgan so'rov yo'q.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    text = f"⏳ <b>Kutilayotgan so'rovlar</b>\n\nJami: {len(requests)} ta\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=withdrawal_requests_keyboard(requests),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view_withdrawal_"))
async def view_withdrawal_handler(callback: CallbackQuery):
    """Pul chiqarish so'rovini ko'rish"""
    if not is_admin(callback.from_user.id):
        return
    
    request_id = int(callback.data.replace("view_withdrawal_", ""))
    
    from database import get_withdrawal_request
    from keyboards import withdrawal_action_keyboard
    
    req = get_withdrawal_request(request_id)
    
    if not req:
        await callback.answer("? So'rov topilmadi!", show_alert=True)
        return
    
    user_name = req['full_name'] if req['full_name'] else "Noma'lum"
    username = f"@{req['username']}" if req['username'] else ""
    card = req['card_number']
    formatted_card = f"{card[:4]} {card[4:8]} {card[8:12]} {card[12:]}"
    
    text = f"""
💵 <b>Pul chiqarish so'rovi #{request_id}</b>

👤 <b>Foydalanuvchi:</b> {user_name} {username}
🆔 <b>ID:</b> <code>{req['user_id']}</code>
💰 <b>Summa:</b> <b>{req['amount']:,} so'm</b>
💳 <b>Karta:</b> <code>{formatted_card}</code>
📅 <b>Sana:</b> {req['created_date'][:16] if req['created_date'] else ""}
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=withdrawal_action_keyboard(request_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("approve_withdrawal_"))
async def approve_withdrawal_handler(callback: CallbackQuery):
    """Pul chiqarishni tasdiqlash"""
    if not is_admin(callback.from_user.id):
        return
    
    request_id = int(callback.data.replace("approve_withdrawal_", ""))
    
    from database import get_withdrawal_request, approve_withdrawal
    
    req = get_withdrawal_request(request_id)
    if not req:
        await callback.answer("? So'rov topilmadi!", show_alert=True)
        return
    
    success = approve_withdrawal(request_id, callback.from_user.id)
    
    if success:
        await callback.answer("? Tasdiqlandi!", show_alert=True)
        
        # Foydalanuvchiga xabar
        try:
            await callback.bot.send_message(
                req['user_id'],
                f"? <b>Pul chiqarish so'rovingiz tasdiqlandi!</b>\n\n"
                f"💰 Summa: <b>{req['amount']:,} so'm</b>\n"
                f"💳 Karta: ****{req['card_number'][-4:]}\n\n"
                f"✅ Tez orada kartangizga o'tkaziladi!",
                parse_mode="HTML"
            )
        except:
            pass
        
        # So'rovlar ro'yxatiga qaytish
        await referral_requests_handler(callback)
    else:
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)


@router.callback_query(F.data.startswith("reject_withdrawal_"))
async def reject_withdrawal_handler(callback: CallbackQuery):
    """Pul chiqarishni rad etish"""
    if not is_admin(callback.from_user.id):
        return
    
    request_id = int(callback.data.replace("reject_withdrawal_", ""))
    
    from database import get_withdrawal_request, reject_withdrawal
    
    req = get_withdrawal_request(request_id)
    if not req:
        await callback.answer("? So'rov topilmadi!", show_alert=True)
        return
    
    success = reject_withdrawal(request_id, callback.from_user.id)
    
    if success:
        await callback.answer("? Rad etildi!", show_alert=True)
        
        # Foydalanuvchiga xabar
        try:
            await callback.bot.send_message(
                req['user_id'],
                f"? <b>Pul chiqarish so'rovingiz rad etildi!</b>\n\n"
                f"💰 Summa: <b>{req['amount']:,} so'm</b>\n\n"
                f"↩️ Pul hisobingizga qaytarildi.",
                parse_mode="HTML"
            )
        except:
            pass
        
        # So'rovlar ro'yxatiga qaytish
        await referral_requests_handler(callback)
    else:
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)


@router.callback_query(F.data == "referral_top")
async def referral_top_handler(callback: CallbackQuery):
    """Top referralchilar"""
    if not is_admin(callback.from_user.id):
        return
    
    from database import get_total_referral_stats
    stats = get_total_referral_stats()
    
    text = "🏆 <b>Top referralchilar</b>\n\n"
    
    if stats['top_referrers']:
        for i, ref in enumerate(stats['top_referrers'], 1):
            name = ref['full_name'] if ref['full_name'] else "Noma'lum"
            username = f"@{ref['username']}" if ref['username'] else ""
            text += f"{i}. {name} {username}\n"
            text += f"   L 👥 {ref['ref_count']} ta referal\n"
    else:
        text += "Hali referal yo'q."
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_referral")]
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "referral_status_info")
async def referral_status_info_handler(callback: CallbackQuery):
    """Referal holati haqida ma'lumot"""
    await callback.answer(
        "💡 Referal tizimi yoqilsa, foydalanuvchilar do'stlarini taklif qilib pul ishlashlari mumkin!",
        show_alert=True
    )


@router.callback_query(F.data == "referral_edit_message")
async def referral_edit_message_handler(callback: CallbackQuery, state: FSMContext):
    """Referal xabarini tahrirlash"""
    if not is_admin(callback.from_user.id):
        return
    
    from states import EditReferralMessage
    from database import get_referral_message
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    current_message = get_referral_message()
    
    cancel_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="referral_settings")]
        ]
    )
    
    await state.set_state(EditReferralMessage.waiting_for_message)
    await callback.message.edit_text(
        f"📝 <b>Referal xabarini tahrirlash</b>\n\n"
        f"Hozirgi xabar:\n"
        f"<i>{current_message}</i>\n\n"
        f"Yangi xabarni yuboring:\n\n"
        f"ℹ️ Bu xabar foydalanuvchi referal havolasini olganda ko'rinadi.",
        reply_markup=cancel_keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(EditReferralMessage.waiting_for_message)
async def referral_message_receiver(message: Message, state: FSMContext):
    """Referal xabarini qabul qilish"""
    if not is_admin(message.from_user.id):
        return
    
    from database import set_referral_message
    
    new_message = message.text or message.caption or ""
    
    if not new_message:
        await message.answer("? Xabar bo'sh bo'lishi mumkin emas!")
        return
    
    set_referral_message(new_message)
    
    await state.clear()
    await message.answer(
        f"? <b>Referal xabari saqlandi!</b>\n\n"
        f"Yangi xabar:\n<i>{new_message}</i>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


# ===== START XABARI MESSAGE HANDLERS =====

@router.message(EditStartMessage.waiting_for_content, F.photo)
async def start_message_photo_receiver(message: Message, state: FSMContext):
    """Start xabari - rasm qabul qilish"""
    if not is_admin(message.from_user.id):
        return
    
    from database import set_start_media, set_start_message, get_start_message
    from keyboards import start_message_keyboard
    
    data = await state.get_data()
    content_type = data.get('content_type', 'photo')
    
    # Rasmni saqlash
    photo = message.photo[-1]  # Eng katta rasm
    set_start_media('photo', photo.file_id)
    
    # Caption bo'lsa, matnni ham yangilash
    if message.caption:
        set_start_message(message.caption)
    
    await state.clear()
    
    current_message = get_start_message()
    
    await message.answer(
        f"? <b>Rasm saqlandi!</b>\n\n"
        f"<b>Start xabari matni:</b>\n<i>{current_message}</i>",
        reply_markup=start_message_keyboard(True),
        parse_mode="HTML"
    )


@router.message(EditStartMessage.waiting_for_content, F.animation)
async def start_message_gif_receiver(message: Message, state: FSMContext):
    """Start xabari - GIF qabul qilish"""
    if not is_admin(message.from_user.id):
        return
    
    from database import set_start_media, set_start_message, get_start_message
    from keyboards import start_message_keyboard
    
    # GIFni saqlash
    set_start_media('animation', message.animation.file_id)
    
    # Caption bo'lsa, matnni ham yangilash
    if message.caption:
        set_start_message(message.caption)
    
    await state.clear()
    
    current_message = get_start_message()
    
    await message.answer(
        f"? <b>GIF saqlandi!</b>\n\n"
        f"<b>Start xabari matni:</b>\n<i>{current_message}</i>",
        reply_markup=start_message_keyboard(True),
        parse_mode="HTML"
    )


@router.message(EditStartMessage.waiting_for_content, F.text)
async def start_message_text_receiver(message: Message, state: FSMContext):
    """Start xabari - matn qabul qilish"""
    if not is_admin(message.from_user.id):
        return
    
    from database import set_start_message, get_start_media
    from keyboards import start_message_keyboard
    
    data = await state.get_data()
    content_type = data.get('content_type', 'text')
    
    # Agar rasm/gif kutilayotgan bo'lsa
    if content_type in ['photo', 'gif']:
        await message.answer(
            "? Iltimos, rasm yoki GIF yuboring!\n\n"
            "Yoki matnni tahrirlash uchun 📝 Matnni tahrirlash tugmasini bosing.",
            parse_mode="HTML"
        )
        return
    
    # Matnni saqlash
    set_start_message(message.text)
    
    await state.clear()
    
    has_media = get_start_media() is not None
    
    await message.answer(
        f"? <b>Start xabari matni saqlandi!</b>\n\n"
        f"<b>Yangi matn:</b>\n<i>{message.text}</i>",
        reply_markup=start_message_keyboard(has_media),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_settings")
async def admin_settings_handler(callback: CallbackQuery):
    """Bot sozlamalari"""
    await callback.answer("⚙️ Sozlamalar bo'limi tez orada!", show_alert=True)


@router.callback_query(F.data.in_({"stats_users", "stats_movies", "stats_today", "stats_weekly"}))
async def stats_details_handler(callback: CallbackQuery):
    """Statistika tafsilotlari"""
    await admin_stats_handler(callback)


@router.callback_query(F.data == "channel_add_link")
async def channel_add_link_handler(callback: CallbackQuery, state: FSMContext):
    """Havola orqali kanal qo'shish"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.set_state(AddChannelLink.waiting_for_url)
    await callback.message.answer(
        "🔗 <b>Havola orqali kanal/sahifa qo'shish</b>\n\n"
        "Havola yuboring:\n\n"
        "Masalan:\n"
        "� https://t.me/channel_name\n"
        "� https://instagram.com/username\n"
        "� https://youtube.com/@channel\n"
        "� Boshqa ijtimoiy tarmoqlar",
        reply_markup=cancel_reply_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddChannelLink.waiting_for_url)
async def add_channel_link(message: Message, state: FSMContext):
    """Havola orqali kanal saqlash"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    text = message.text.strip()
    
    # Havola formatini tekshirish
    if not text.startswith("http://") and not text.startswith("https://") and not text.startswith("@"):
        await message.answer(
            "❌ Noto'g'ri format!\n\n"
            "Havola http:// yoki https:// bilan boshlanishi kerak.\n"
            "Yoki @username formatida yuboring.",
            reply_markup=cancel_reply_keyboard()
        )
        return
    
    # Telegram havolasimi tekshirish
    is_telegram = "t.me" in text or text.startswith("@")
    
    if is_telegram:
        # Telegram kanal uchun
        if text.startswith("https://t.me/"):
            username = text.replace("https://t.me/", "").split("/")[0].split("?")[0]
        elif text.startswith("@"):
            username = text[1:]
        else:
            username = text
        
        try:
            chat = await message.bot.get_chat(f"@{username}")
            url = f"https://t.me/{username}"
            success = add_channel(
                channel_id=chat.id,
                channel_username=username,
                title=chat.title,
                url=url
            )
            
            if success:
                await message.answer(
                    f"✅ Kanal qo'shildi!\n\n"
                    f"🎬 Nomi: {chat.title}\n"
                    f"🔗 Havola: {url}\n"
                    f"🆔 ID: <code>{chat.id}</code>",
                    reply_markup=admin_menu_keyboard(),
                    parse_mode="HTML"
                )
            else:
                await message.answer(
                    "⚠️ Bu kanal allaqachon qo'shilgan!",
                    reply_markup=admin_menu_keyboard()
                )
            await state.clear()
            return
        except Exception:
            pass  # Telegram kanal topilmadi, oddiy havola sifatida saqlaymiz
    
    # Instagram, YouTube yoki boshqa havolalar
    # Havola nomini aniqlash
    if "instagram.com" in text:
        platform = "📸 Instagram"
        title = text.split("instagram.com/")[-1].split("/")[0].split("?")[0]
    elif "youtube.com" in text or "youtu.be" in text:
        platform = "▶️ YouTube"
        if "youtube.com/@" in text:
            title = text.split("@")[-1].split("/")[0].split("?")[0]
        elif "youtube.com/channel/" in text:
            title = "YouTube kanal"
        else:
            title = "YouTube"
    elif "tiktok.com" in text:
        platform = "🎵 TikTok"
        title = text.split("tiktok.com/@")[-1].split("/")[0].split("?")[0] if "@" in text else "TikTok"
    elif "facebook.com" in text:
        platform = "📘 Facebook"
        title = "Facebook"
    else:
        platform = "🔗 Havola"
        title = text.split("//")[-1].split("/")[0]
    
    # Unique ID yaratish
    import hashlib
    unique_id = int(hashlib.md5(text.encode()).hexdigest()[:8], 16) * -1
    
    success = add_channel(
        channel_id=unique_id,
        channel_username=None,
        title=f"{platform}: {title}",
        url=text,
        invite_link=text,
        is_request_group=False,
        is_external_link=True
    )
    
    if success:
        await message.answer(
            f"? Havola qo'shildi!\n\n"
            f"📱 Platforma: {platform}\n"
            f"🔗 Havola: {text}\n\n"
            f"ℹ️ Eslatma: Bu tashqi havola, obuna tekshirilmaydi.",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "⚠️ Bu havola allaqachon qo'shilgan!",
            reply_markup=admin_menu_keyboard()
        )
    
    await state.clear()


@router.callback_query(F.data == "channel_request_group")
async def channel_request_group_handler(callback: CallbackQuery, state: FSMContext):
    """So'rovli guruh qo'shish"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.set_state(AddRequestGroup.waiting_for_group)
    await callback.message.answer(
        "📝 <b>So'rovli guruh/kanal qo'shish</b>\n\n"
        "Bu funksiya orqali foydalanuvchilar guruh/kanalga qo'shilish so'rovi yuboradi.\n\n"
        "ℹ️ <b>Qanday ishlaydi:</b>\n"
        "1. Bot guruh/kanalda admin bo'lishi kerak\n"
        "2. Guruh/kanalda 'Taklif havolalari' orqali yangi havola yarating\n"
        "3. 'Admin tasdiqlashini so'rash' ni yoqing\n"
        "4. Shu havolani bu yerga yuboring\n\n"
        "📌 Birinchi navbatda botni guruh/kanalga admin qilib qo'shing\n"
        "So'ng guruh/kanaldan xabar forward qiling:",
        reply_markup=cancel_reply_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddRequestGroup.waiting_for_group)
async def add_request_group_forward(message: Message, state: FSMContext):
    """Forward qilingan xabardan guruh ma'lumotlarini olish"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    # Forward qilingan xabar tekshirish
    if message.forward_from_chat:
        chat = message.forward_from_chat
        chat_id = chat.id
        title = chat.title
        
        await state.update_data(chat_id=chat_id, title=title)
        await state.set_state(AddRequestGroup.waiting_for_invite_link)
        
        await message.answer(
            f"? <b>{title}</b> topildi!\n\n"
            "Endi shu guruh/kanal uchun so'rovli havola yuboring:\n"
            "<i>Masalan: https://t.me/+ABC123xyz</i>",
            reply_markup=cancel_reply_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "⚠️ Iltimos, guruh/kanaldan xabar forward qiling!\n\n"
            "Yoki bekor qilish uchun tugmani bosing:",
            reply_markup=cancel_reply_keyboard()
        )


@router.message(AddRequestGroup.waiting_for_invite_link)
async def add_request_group_link(message: Message, state: FSMContext):
    """So'rovli guruh havolasini saqlash"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    invite_link = message.text.strip()
    
    # Havola formatini tekshirish
    if not invite_link.startswith("https://t.me/+") and not invite_link.startswith("t.me/+"):
        await message.answer(
            "❌ Noto'g'ri havola formati!\n\n"
            "Havola bunday bo'lishi kerak:\n"
            "<code>https://t.me/+ABC123xyz</code>",
            parse_mode="HTML"
        )
        return
    
    if not invite_link.startswith("https://"):
        invite_link = "https://" + invite_link
    
    # State dan ma'lumotlarni olish
    data = await state.get_data()
    chat_id = data.get('chat_id')
    title = data.get('title')
    
    # Database ga saqlash
    success = add_channel(
        channel_id=chat_id,
        channel_username=None,
        title=f"📺 {title}",
        url=invite_link,
        invite_link=invite_link,
        is_request_group=True
    )
    
    if success:
        await message.answer(
            f"? So'rovli guruh/kanal qo'shildi!\n\n"
            f"🎬 Nomi: {title}\n"
            f"🔗 Havola: {invite_link}\n\n"
            f"ℹ️ Foydalanuvchilar majburiy obuna ro'yxatida shu havolani ko'radi.\n"
            f"Ular qo'shilish so'rovi yuboradi, bot avtomatik tasdiqlaydi.",
            reply_markup=admin_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "⚠️ Bu guruh/kanal allaqachon qo'shilgan!",
            reply_markup=admin_menu_keyboard()
        )
    
    await state.clear()


@router.callback_query(F.data == "movie_channel_button")
async def movie_channel_button_handler(callback: CallbackQuery):
    """Kanal tugmasi sozlamalari"""
    if not is_admin(callback.from_user.id):
        return
    
    is_enabled = is_channel_button_enabled()
    btn_text = get_channel_button_text()
    btn_url = get_channel_button_url()
    
    status = "? Yoniq" if is_enabled else "? O'chiq"
    
    text = (
        f"🔘 <b>Kanal tugmasi sozlamalari</b>\n\n"
        f"📊 Holati: {status}\n"
        f"📝 Matn: {btn_text}\n"
        f"🔗 Havola: {btn_url if btn_url else 'Kiritilmagan'}\n\n"
        f"ℹ️ Yoniq bo'lganda foydalanuvchilarga kino yuborilganda video ostida tugma chiqadi."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=channel_button_settings_keyboard(is_enabled),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "channel_btn_status")
async def channel_btn_status_handler(callback: CallbackQuery):
    """Kanal tugmasi status"""
    await callback.answer()


@router.callback_query(F.data == "channel_btn_toggle")
async def channel_btn_toggle_handler(callback: CallbackQuery):
    """Kanal tugmasini yoniq/o'chiq qilish"""
    if not is_admin(callback.from_user.id):
        return
    
    new_status = toggle_channel_button()
    is_enabled = new_status
    btn_text = get_channel_button_text()
    btn_url = get_channel_button_url()
    
    status = "? Yoniq" if is_enabled else "? O'chiq"
    
    text = (
        f"🔘 <b>Kanal tugmasi sozlamalari</b>\n\n"
        f"📊 Holati: {status}\n"
        f"📝 Matn: {btn_text}\n"
        f"🔗 Havola: {btn_url if btn_url else 'Kiritilmagan'}\n\n"
        f"ℹ️ Yoniq bo'lganda foydalanuvchilarga kino yuborilganda video ostida tugma chiqadi."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=channel_button_settings_keyboard(is_enabled),
        parse_mode="HTML"
    )
    status_text = "yoqildi" if is_enabled else "o'chirildi"
    await callback.answer(f"? Kanal tugmasi {status_text}!")


class EditChannelButton:
    """Kanal tugmasi tahrirlash states"""
    pass


from states import AddMovie, DeleteMovie, Broadcast, AddChannel, SetBaseChannel
from aiogram.fsm.state import State, StatesGroup


class EditChannelButtonState(StatesGroup):
    waiting_for_text = State()
    waiting_for_url = State()


@router.callback_query(F.data == "channel_btn_edit_text")
async def channel_btn_edit_text_handler(callback: CallbackQuery, state: FSMContext):
    """Kanal tugmasi matnini tahrirlash"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.set_state(EditChannelButtonState.waiting_for_text)
    await callback.message.answer(
        "📝 Yangi tugma matnini kiriting:\n\n"
        f"Hozirgi: {get_channel_button_text()}",
        reply_markup=cancel_reply_keyboard()
    )
    await callback.answer()


@router.message(EditChannelButtonState.waiting_for_text)
async def set_channel_btn_text(message: Message, state: FSMContext):
    """Kanal tugmasi matnini saqlash"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    set_channel_button_text(message.text.strip())
    await state.clear()
    await message.answer(
        f"? Tugma matni yangilandi: {message.text.strip()}",
        reply_markup=admin_menu_keyboard()
    )


@router.callback_query(F.data == "channel_btn_edit_url")
async def channel_btn_edit_url_handler(callback: CallbackQuery, state: FSMContext):
    """Kanal tugmasi havolasini tahrirlash"""
    if not is_admin(callback.from_user.id):
        return
    
    current_url = get_channel_button_url()
    await state.set_state(EditChannelButtonState.waiting_for_url)
    await callback.message.answer(
        "🔗 Yangi havola kiriting:\n\n"
        f"Hozirgi: {current_url if current_url else 'Kiritilmagan'}\n\n"
        "Masalan: https://t.me/your_channel",
        reply_markup=cancel_reply_keyboard()
    )
    await callback.answer()


@router.message(EditChannelButtonState.waiting_for_url)
async def set_channel_btn_url(message: Message, state: FSMContext):
    """Kanal tugmasi havolasini saqlash"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    url = message.text.strip()
    if not url.startswith("https://") and not url.startswith("http://"):
        url = "https://" + url
    
    set_channel_button_url(url)
    await state.clear()
    await message.answer(
        f"? Tugma havolasi yangilandi: {url}",
        reply_markup=admin_menu_keyboard()
    )


# ===== PREMIUM BOSHQARUVI =====

@router.callback_query(F.data == "toggle_premium")
async def toggle_premium_handler(callback: CallbackQuery):
    """Premium tizimini yoqish/o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    
    current = is_premium_enabled()
    set_premium_enabled(not current)
    new_status = "yoqildi ?" if not current else "o'chirildi ?"
    
    await callback.answer(f"Premium tizimi {new_status}", show_alert=True)
    
    # Klaviaturani yangilash
    from keyboards import premium_management_keyboard
    await callback.message.edit_reply_markup(reply_markup=premium_management_keyboard(not current))


@router.callback_query(F.data == "admin_premium")
async def admin_premium_callback(callback: CallbackQuery):
    """Premium boshqaruvi - Inline"""
    if not is_admin(callback.from_user.id):
        return
    
    from keyboards import premium_management_keyboard
    enabled = is_premium_enabled()
    premium_count = get_premium_users_count()
    pending = len(get_pending_premium_requests())
    plans = get_all_premium_plans()
    card = get_payment_card()
    
    text = f"""
💎 <b>Premium Obuna Boshqaruvi</b>

📊 <b>Statistika:</b>
+ Premium foydalanuvchilar: <code>{premium_count}</code>
+ Kutilayotgan so'rovlar: <code>{pending}</code>
L Tariflar soni: <code>{len(plans)}</code>

💳 <b>To'lov kartasi:</b> <code>{card if card else "Sozlanmagan"}</code>
"""
    await callback.message.edit_text(text, reply_markup=premium_management_keyboard(enabled), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "premium_plans")
async def premium_plans_handler(callback: CallbackQuery):
    """Tariflar ro'yxati"""
    if not is_admin(callback.from_user.id):
        return
    
    from keyboards import premium_plans_keyboard
    plans = get_all_premium_plans()
    
    if not plans:
        await callback.answer("Tariflar mavjud emas. Yangi tarif qo'shing.", show_alert=True)
        return
    
    text = "💎 <b>Premium Tariflar:</b>\n\n"
    for plan in plans:
        text += f"💎 <b>{plan['name']}</b>\n"
        text += f"   🆔 Narx: {plan['price']:,} so'm\n"
        text += f"   🆔 Muddat: {plan['duration_days']} kun\n\n"
    
    await callback.message.edit_text(text, reply_markup=premium_plans_keyboard(plans), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "add_premium_plan")
async def add_premium_plan_handler(callback: CallbackQuery, state: FSMContext):
    """Yangi tarif qo'shish"""
    if not is_admin(callback.from_user.id):
        return
    
    await state.set_state(AddPremiumPlan.waiting_for_name)
    await callback.message.answer(
        "➕ <b>Yangi tarif qo'shish</b>\n\n"
        "1️⃣ Tarif nomini kiriting:",
        reply_markup=cancel_reply_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddPremiumPlan.waiting_for_name)
async def premium_plan_name_handler(message: Message, state: FSMContext):
    """Tarif nomi"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    await state.update_data(name=message.text)
    await state.set_state(AddPremiumPlan.waiting_for_duration)
    await message.answer(
        "2️⃣ Tarif muddatini kiriting (kun):\n\n"
        "Masalan: 30"
    )


@router.message(AddPremiumPlan.waiting_for_duration)
async def premium_plan_duration_handler(message: Message, state: FSMContext):
    """Tarif muddati"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    try:
        duration = int(message.text)
        if duration <= 0:
            raise ValueError
    except ValueError:
        await message.answer("? Noto'g'ri format. Musbat son kiriting:")
        return
    
    await state.update_data(duration=duration)
    await state.set_state(AddPremiumPlan.waiting_for_price)
    await message.answer(
        "3️⃣ Tarif narxini kiriting (so'm):\n\n"
        "Masalan: 50000"
    )


@router.message(AddPremiumPlan.waiting_for_price)
async def premium_plan_price_handler(message: Message, state: FSMContext):
    """Tarif narxi"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    try:
        price = int(message.text.replace(" ", "").replace(",", ""))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("? Noto'g'ri format. Musbat son kiriting:")
        return
    
    data = await state.get_data()
    name = data['name']
    duration = data['duration']
    
    success = add_premium_plan(name, duration, price)
    
    if success:
        await message.answer(
            f"? Tarif qo'shildi!\n\n"
            f"🎬 Nomi: {name}\n"
            f"⏱ Muddat: {duration} kun\n"
            f"💰 Narx: {price:,} so'm",
            reply_markup=admin_menu_keyboard()
        )
    else:
        await message.answer("? Xatolik yuz berdi", reply_markup=admin_menu_keyboard())
    
    await state.clear()


@router.callback_query(F.data.startswith("view_plan_"))
async def view_plan_handler(callback: CallbackQuery):
    """Tarif ko'rish"""
    if not is_admin(callback.from_user.id):
        return
    
    plan_id = int(callback.data.replace("view_plan_", ""))
    plan = get_premium_plan(plan_id)
    
    if not plan:
        await callback.answer("Tarif topilmadi", show_alert=True)
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delete_plan_{plan_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="premium_plans")]
    ])
    
    text = f"""
💎 <b>{plan['name']}</b>

💰 Narx: <b>{plan['price']:,} so'm</b>
⏱ Muddat: <b>{plan['duration_days']} kun</b>
"""
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("delete_plan_"))
async def delete_plan_handler(callback: CallbackQuery):
    """Tarifni o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    
    plan_id = int(callback.data.replace("delete_plan_", ""))
    success = delete_premium_plan(plan_id)
    
    if success:
        await callback.answer("? Tarif o'chirildi", show_alert=True)
    else:
        await callback.answer("? Xatolik", show_alert=True)
    
    # Tariflar ro'yxatiga qaytish
    from keyboards import premium_plans_keyboard
    plans = get_all_premium_plans()
    
    if plans:
        text = "💎 <b>Premium Tariflar:</b>\n\n"
        for plan in plans:
            text += f"💎 <b>{plan['name']}</b>\n"
            text += f"   🆔 Narx: {plan['price']:,} so'm\n"
            text += f"   🆔 Muddat: {plan['duration_days']} kun\n\n"
        await callback.message.edit_text(text, reply_markup=premium_plans_keyboard(plans), parse_mode="HTML")
    else:
        from keyboards import premium_management_keyboard
        await callback.message.edit_text(
            "❌ Tariflar mavjud emas.",
            reply_markup=premium_management_keyboard(is_premium_enabled())
        )


@router.callback_query(F.data == "set_payment_card")
async def set_payment_card_handler(callback: CallbackQuery, state: FSMContext):
    """To'lov kartasini sozlash"""
    if not is_admin(callback.from_user.id):
        return
    
    current_card = get_payment_card()
    await state.set_state(SetPaymentCard.waiting_for_card)
    await callback.message.answer(
        f"💳 <b>To'lov kartasini kiriting:</b>\n\n"
        f"Hozirgi: <code>{current_card if current_card else 'Kiritilmagan'}</code>\n\n"
        f"Masalan: 8600 1234 5678 9012",
        reply_markup=cancel_reply_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(SetPaymentCard.waiting_for_card)
async def payment_card_handler(message: Message, state: FSMContext):
    """To'lov kartasini saqlash"""
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
        return
    
    card = message.text.strip()
    set_payment_card(card)
    await state.clear()
    await message.answer(
        f"? To'lov kartasi saqlandi:\n<code>{card}</code>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "pending_premium_requests")
async def pending_premium_requests_handler(callback: CallbackQuery):
    """Kutilayotgan so'rovlar"""
    if not is_admin(callback.from_user.id):
        return
    
    requests = get_pending_premium_requests()
    
    if not requests:
        await callback.answer("Kutilayotgan so'rovlar yo'q", show_alert=True)
        return
    
    text = f"⏳ <b>Kutilayotgan so'rovlar:</b> {len(requests)} ta\n\n"
    text += "So'rovlarni ko'rish uchun kutib turing..."
    
    await callback.answer(f"{len(requests)} ta so'rov mavjud")
    
    # Har bir so'rovni yuborish
    from keyboards import premium_request_keyboard
    for req in requests:
        req_text = f"""
💎 <b>Premium so'rov #{req['id']}</b>

👤 Foydalanuvchi: {req['full_name']}
📝 Username: @{req['username'] if req['username'] else "yo'q"}
🆔 ID: <code>{req['user_id']}</code>

💎 Tarif: {req['plan_name']}
💰 Narx: {req['price']:,} so'm
⏱ Muddat: {req['duration_days']} kun

📅 Yuborilgan: {req['created_date']}
"""
        try:
            if req['file_type'] == 'photo':
                await callback.message.answer_photo(
                    req['file_id'],
                    caption=req_text,
                    reply_markup=premium_request_keyboard(req['id']),
                    parse_mode="HTML"
                )
            else:
                await callback.message.answer_document(
                    req['file_id'],
                    caption=req_text,
                    reply_markup=premium_request_keyboard(req['id']),
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"So'rov yuborishda xatolik: {e}")


@router.callback_query(F.data.startswith("approve_premium_"))
async def approve_premium_handler(callback: CallbackQuery):
    """Premium so'rovni tasdiqlash"""
    if not is_admin(callback.from_user.id):
        return
    
    request_id = int(callback.data.replace("approve_premium_", ""))
    req = get_premium_request(request_id)
    
    if not req:
        await callback.answer("So'rov topilmadi", show_alert=True)
        return
    
    success = approve_premium_request(request_id, callback.from_user.id)
    
    if success:
        await callback.answer("? Tasdiqlandi!", show_alert=True)
        
        # Tugmalarni o'chirish
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n? <b>TASDIQLANDI</b>",
            parse_mode="HTML"
        )
        
        # Foydalanuvchiga xabar
        try:
            await callback.bot.send_message(
                req['user_id'],
                f"🎉 <b>Tabriklaymiz!</b>\n\n"
                f"Sizning Premium obunangiz tasdiqlandi!\n"
                f"💎 Tarif: {req['plan_name']}\n"
                f"⏱ Muddat: {req['duration_days']} kun\n\n"
                f"Endi sizda majburiy obuna talab qilinmaydi! ?",
                parse_mode="HTML"
            )
        except:
            pass
    else:
        await callback.answer("? Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data.startswith("reject_premium_"))
async def reject_premium_handler(callback: CallbackQuery):
    """Premium so'rovni rad etish"""
    if not is_admin(callback.from_user.id):
        return
    
    request_id = int(callback.data.replace("reject_premium_", ""))
    req = get_premium_request(request_id)
    
    if not req:
        await callback.answer("So'rov topilmadi", show_alert=True)
        return
    
    success = reject_premium_request(request_id, callback.from_user.id)
    
    if success:
        await callback.answer("? Rad etildi", show_alert=True)
        
        # Tugmalarni o'chirish
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n? <b>RAD ETILDI</b>",
            parse_mode="HTML"
        )
        
        # Foydalanuvchiga xabar
        try:
            await callback.bot.send_message(
                req['user_id'],
                "? <b>Afsus!</b>\n\n"
                "Sizning Premium so'rovingiz rad etildi.\n"
                "To'lov cheki noto'g'ri yoki muvofiq emas.\n\n"
                "Iltimos, qaytadan urinib ko'ring yoki admin bilan bog'laning.",
                parse_mode="HTML"
            )
        except:
            pass
    else:
        await callback.answer("? Xatolik yuz berdi", show_alert=True)


@router.callback_query(F.data == "premium_users_list")
async def premium_users_list_handler(callback: CallbackQuery):
    """Premium foydalanuvchilar ro'yxati"""
    if not is_admin(callback.from_user.id):
        return
    
    from database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ps.*, u.full_name, u.username, pp.name as plan_name
        FROM premium_subscriptions ps
        JOIN users u ON ps.user_id = u.user_id
        LEFT JOIN premium_plans pp ON ps.plan_id = pp.id
        WHERE ps.is_active = 1 AND ps.end_date > CURRENT_TIMESTAMP
        ORDER BY ps.end_date DESC
    ''')
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        await callback.answer("Premium foydalanuvchilar yo'q", show_alert=True)
        return
    
    text = f"💎 <b>Premium Foydalanuvchilar:</b> {len(users)} ta\n\n"
    
    for user in users:
        text += f"👤 {user['full_name']}\n"
        text += f"   🆔 @{user['username'] if user['username'] else 'yo`q'}\n"
        text += f"   🆔 {user['plan_name'] if user['plan_name'] else 'Tarif yo`q'}\n"
        text += f"   🆔 Tugash: {user['end_date'][:10]}\n\n"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_premium")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ==================== BACKUP (ZAXIRA) HANDLERLARI ====================

@router.message(F.text == "🗄 Zaxira nusxa")
async def backup_menu_handler(message: Message):
    """Zaxira nusxa boshqaruvi"""
    if not is_admin(message.from_user.id):
        return
    
    stats = backup.get_backup_stats()
    
    text = f"""
🗄 <b>Zaxira nusxa boshqaruvi</b>

📦 Jami zaxiralar: {stats['total_backups']} ta
💾 Umumiy hajm: {stats['total_size_mb']} MB
"""
    
    if stats['latest_backup']:
        text += f"📅 Oxirgi zaxira: {stats['latest_backup']['created']}\n"
    
    text += """
⚠️ <b>Muhim:</b> Zaxira nusxa serverdan boshqa joyga ko'chganda yoki server o'chganda ma'lumotlarni tiklash uchun kerak.

<b>Tavsiya:</b> Har kuni avtomatik zaxira Telegramga yuborilsin!
"""
    
    await message.answer(text, reply_markup=backup_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "admin_backup")
async def backup_callback_handler(callback: CallbackQuery):
    """Zaxira nusxa boshqaruvi (callback)"""
    if not is_admin(callback.from_user.id):
        return
    
    stats = backup.get_backup_stats()
    
    text = f"""
🗄 <b>Zaxira nusxa boshqaruvi</b>

📦 Jami zaxiralar: {stats['total_backups']} ta
💾 Umumiy hajm: {stats['total_size_mb']} MB
"""
    
    if stats['latest_backup']:
        text += f"📅 Oxirgi zaxira: {stats['latest_backup']['created']}\n"
    
    await callback.message.edit_text(text, reply_markup=backup_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "backup_create")
async def backup_create_handler(callback: CallbackQuery):
    """Zaxira yaratish va Telegramga yuborish"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.answer("⏳ Zaxira yaratilmoqda...", show_alert=False)
    
    try:
        # Backup yaratish
        db_path = backup.create_backup()
        
        if db_path:
            # Telegramga yuborish
            import os
            from datetime import datetime
            
            stats = backup.get_backup_stats()
            users_count = get_users_count()
            movies_count = get_movies_count()
            
            caption = f"""🗄 Zaxira nusxa yaratildi!

📅 Sana: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
👥 Foydalanuvchilar: {users_count}
🎬 Kinolar: {movies_count}
💾 Fayl hajmi: {stats['latest_backup']['size_mb']} MB

✅ Ushbu faylni saqlang!
Boshqa serverga o'tkazganda shu fayl orqali tiklash mumkin."""
            
            document = FSInputFile(db_path)
            await callback.bot.send_document(
                chat_id=callback.from_user.id,
                document=document,
                caption=caption
            )
            
            await callback.message.edit_text(
                "✅ <b>Zaxira muvaffaqiyatli yaratildi!</b>\n\n"
                "Fayl sizga yuborildi. Uni xavfsiz joyda saqlang.",
                reply_markup=backup_keyboard(),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ Zaxira yaratishda xatolik!",
                reply_markup=backup_keyboard(),
                parse_mode="HTML"
            )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Xatolik: {e}",
            reply_markup=backup_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "backup_json")
async def backup_json_handler(callback: CallbackQuery):
    """JSON formatda zaxira yaratish"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.answer("⏳ JSON zaxira yaratilmoqda...", show_alert=False)
    
    try:
        json_path = backup.create_json_backup()
        
        if json_path:
            from datetime import datetime
            
            caption = f"""📋 JSON Zaxira

📅 Sana: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

ℹ️ Bu format boshqa tizimga ma'lumotlarni ko'chirish uchun qulay.
O'qish va tahrirlash oson."""
            
            document = FSInputFile(json_path)
            await callback.bot.send_document(
                chat_id=callback.from_user.id,
                document=document,
                caption=caption
            )
            
            await callback.message.edit_text(
                "✅ <b>JSON zaxira yaratildi!</b>\n\n"
                "Fayl sizga yuborildi.",
                reply_markup=backup_keyboard(),
                parse_mode="HTML"
            )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Xatolik: {e}",
            reply_markup=backup_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "backup_list")
async def backup_list_handler(callback: CallbackQuery):
    """Zaxiralar ro'yxati"""
    if not is_admin(callback.from_user.id):
        return
    
    backups = backup.get_backup_list()
    
    if not backups:
        await callback.answer("Hech qanday zaxira topilmadi!", show_alert=True)
        return
    
    text = f"📁 <b>Zaxiralar ro'yxati:</b> {len(backups)} ta\n\n"
    text += "Tanlang va amal bajaring:\n"
    
    await callback.message.edit_text(
        text, 
        reply_markup=backup_list_keyboard(backups),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("backup_select_"))
async def backup_select_handler(callback: CallbackQuery):
    """Zaxira tanlash"""
    if not is_admin(callback.from_user.id):
        return
    
    index = int(callback.data.split("_")[2])
    backups = backup.get_backup_list()
    
    if index >= len(backups):
        await callback.answer("Zaxira topilmadi!", show_alert=True)
        return
    
    selected = backups[index]
    
    text = f"""
📦 <b>Tanlangan zaxira:</b>

📄 Fayl: {selected['filename']}
💾 Hajmi: {selected['size_mb']} MB
📅 Yaratilgan: {selected['created']}

Nima qilmoqchisiz?
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=backup_action_keyboard(index),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("backup_send_"))
async def backup_send_handler(callback: CallbackQuery):
    """Zaxirani Telegramga yuborish"""
    if not is_admin(callback.from_user.id):
        return
    
    index = int(callback.data.split("_")[2])
    backups = backup.get_backup_list()
    
    if index >= len(backups):
        await callback.answer("Zaxira topilmadi!", show_alert=True)
        return
    
    selected = backups[index]
    
    try:
        document = FSInputFile(selected['path'])
        await callback.bot.send_document(
            chat_id=callback.from_user.id,
            document=document,
            caption=f"📦 Zaxira: {selected['filename']}\n💾 Hajmi: {selected['size_mb']} MB"
        )
        await callback.answer("✅ Yuborildi!", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Xatolik!", show_alert=True)


@router.callback_query(F.data.startswith("backup_do_restore_"))
async def backup_do_restore_handler(callback: CallbackQuery):
    """Zaxiradan tiklash"""
    if not is_admin(callback.from_user.id):
        return
    
    index = int(callback.data.split("_")[3])
    backups = backup.get_backup_list()
    
    if index >= len(backups):
        await callback.answer("Zaxira topilmadi!", show_alert=True)
        return
    
    selected = backups[index]
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, tiklash", callback_data=f"backup_confirm_restore_{index}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="backup_list")
        ]
    ])
    
    await callback.message.edit_text(
        f"⚠️ <b>DIQQAT!</b>\n\n"
        f"Hozirgi barcha ma'lumotlar <b>{selected['filename']}</b> dagi ma'lumotlar bilan almashtiriladi!\n\n"
        f"Davom etasizmi?",
        reply_markup=confirm_kb,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("backup_confirm_restore_"))
async def backup_confirm_restore_handler(callback: CallbackQuery):
    """Tiklashni tasdiqlash"""
    if not is_admin(callback.from_user.id):
        return
    
    index = int(callback.data.split("_")[3])
    backups = backup.get_backup_list()
    
    if index >= len(backups):
        await callback.answer("Zaxira topilmadi!", show_alert=True)
        return
    
    selected = backups[index]
    success, message = backup.restore_from_backup(selected['path'])
    
    if success:
        await callback.message.edit_text(
            f"✅ <b>Muvaffaqiyatli tiklandi!</b>\n\n{message}\n\n"
            f"⚠️ Bot qayta ishga tushirilishi kerak!",
            reply_markup=backup_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"❌ <b>Xatolik!</b>\n\n{message}",
            reply_markup=backup_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("backup_delete_"))
async def backup_delete_handler(callback: CallbackQuery):
    """Zaxirani o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    
    index = int(callback.data.split("_")[2])
    backups = backup.get_backup_list()
    
    if index >= len(backups):
        await callback.answer("Zaxira topilmadi!", show_alert=True)
        return
    
    selected = backups[index]
    
    try:
        import os
        os.remove(selected['path'])
        await callback.answer("✅ O'chirildi!", show_alert=True)
        
        # Ro'yxatni yangilash
        backups = backup.get_backup_list()
        if backups:
            await callback.message.edit_text(
                f"📁 <b>Zaxiralar ro'yxati:</b> {len(backups)} ta\n\nTanlang va amal bajaring:",
                reply_markup=backup_list_keyboard(backups),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "📁 Hech qanday zaxira yo'q",
                reply_markup=backup_keyboard(),
                parse_mode="HTML"
            )
    except Exception as e:
        await callback.answer(f"❌ Xatolik: {e}", show_alert=True)


@router.callback_query(F.data == "backup_stats")
async def backup_stats_handler(callback: CallbackQuery):
    """Zaxira statistikasi"""
    if not is_admin(callback.from_user.id):
        return
    
    stats = backup.get_backup_stats()
    
    text = f"""
📊 <b>Zaxira statistikasi</b>

📦 Jami zaxiralar: {stats['total_backups']} ta
💾 Umumiy hajm: {stats['total_size_mb']} MB
"""
    
    if stats['latest_backup']:
        text += f"\n📅 <b>Oxirgi zaxira:</b>\n"
        text += f"   📄 {stats['latest_backup']['filename']}\n"
        text += f"   💾 {stats['latest_backup']['size_mb']} MB\n"
        text += f"   🕐 {stats['latest_backup']['created']}\n"
    
    if stats['oldest_backup']:
        text += f"\n📅 <b>Eng eski zaxira:</b>\n"
        text += f"   📄 {stats['oldest_backup']['filename']}\n"
        text += f"   💾 {stats['oldest_backup']['size_mb']} MB\n"
        text += f"   🕐 {stats['oldest_backup']['created']}\n"
    
    await callback.message.edit_text(text, reply_markup=backup_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "backup_restore")
async def backup_restore_menu_handler(callback: CallbackQuery):
    """Tiklash menyusi"""
    if not is_admin(callback.from_user.id):
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    text = """
📥 <b>Zaxiradan tiklash</b>

1️⃣ <b>Mavjud zaxiradan:</b> Serverda saqlangan zaxiralardan birini tanlang

2️⃣ <b>Fayl yuborish:</b> Oldin saqlagan .db faylingizni adminga yuboring

⚠️ <b>Eslatma:</b> Tiklashdan oldin hozirgi ma'lumotlar avtomatik zaxiralanadi.
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 Mavjud zaxiralardan", callback_data="backup_list")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_backup")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Fayl orqali tiklash (admin .db fayl yuborsa)
@router.message(F.document)
async def document_handler(message: Message, state: FSMContext):
    """Fayl qabul qilish (backup tiklash uchun)"""
    if not is_admin(message.from_user.id):
        return
    
    # Faqat .db fayl bo'lsa
    if message.document.file_name.endswith('.db'):
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        # Faylni saqlash
        file = await message.bot.get_file(message.document.file_id)
        file_path = f"backups/uploaded_{message.document.file_name}"
        
        backup.create_backup_folder()
        await message.bot.download_file(file.file_path, file_path)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, tiklash", callback_data=f"restore_uploaded_{message.document.file_name}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_backup")
            ]
        ])
        
        await message.answer(
            f"📦 <b>Zaxira fayl qabul qilindi!</b>\n\n"
            f"📄 Fayl: {message.document.file_name}\n\n"
            f"Bu fayldan ma'lumotlarni tiklamoqchimisiz?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("restore_uploaded_"))
async def restore_uploaded_handler(callback: CallbackQuery):
    """Yuklangan fayldan tiklash"""
    if not is_admin(callback.from_user.id):
        return
    
    filename = callback.data.replace("restore_uploaded_", "")
    file_path = f"backups/uploaded_{filename}"
    
    success, message = backup.restore_from_backup(file_path)
    
    if success:
        await callback.message.edit_text(
            f"✅ <b>Muvaffaqiyatli tiklandi!</b>\n\n{message}\n\n"
            f"⚠️ Bot qayta ishga tushirilishi kerak!",
            reply_markup=backup_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"❌ <b>Xatolik!</b>\n\n{message}",
            reply_markup=backup_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()


# ==================== CLOUD BACKUP HANDLERLARI ====================

@router.callback_query(F.data == "backup_cloud")
async def backup_cloud_handler(callback: CallbackQuery):
    """Cloud backup yaratish"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.answer("☁️ Cloud backup yuklanmoqda...", show_alert=False)
    
    try:
        import cloud_backup
        file_id = await cloud_backup.upload_backup_to_cloud(callback.bot)
        
        if file_id:
            await callback.message.edit_text(
                f"☁️ <b>Cloud backup muvaffaqiyatli yuklandi!</b>\n\n"
                f"📦 File ID saqlandi\n"
                f"🔄 Server qayta ishga tushganda avtomatik tiklanadi\n\n"
                f"<b>Qanday ishlaydi:</b>\n"
                f"1. Railway/Heroku qayta deploy qilganda\n"
                f"2. Server o'chib yonsa\n"
                f"3. Database o'chib ketsa\n\n"
                f"Bot avtomatik clouddan tiklaydi! ✅",
                reply_markup=backup_keyboard(),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ Cloud backup yuklashda xatolik!",
                reply_markup=backup_keyboard(),
                parse_mode="HTML"
            )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Xatolik: {e}",
            reply_markup=backup_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "backup_cloud_restore")
async def backup_cloud_restore_handler(callback: CallbackQuery):
    """Clouddan tiklash"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.answer("🔄 Clouddan tiklanmoqda...", show_alert=False)
    
    try:
        import cloud_backup
        
        file_id = cloud_backup.get_last_backup_id()
        
        if not file_id:
            await callback.message.edit_text(
                "❌ <b>Cloud backup topilmadi!</b>\n\n"
                "Avval ☁️ Cloud backup tugmasini bosing.",
                reply_markup=backup_keyboard(),
                parse_mode="HTML"
            )
            return
        
        success = await cloud_backup.restore_from_cloud(callback.bot, file_id)
        
        if success:
            await callback.message.edit_text(
                "✅ <b>Clouddan muvaffaqiyatli tiklandi!</b>\n\n"
                "⚠️ Bot qayta ishga tushirilishi kerak!",
                reply_markup=backup_keyboard(),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "❌ Clouddan tiklashda xatolik!",
                reply_markup=backup_keyboard(),
                parse_mode="HTML"
            )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Xatolik: {e}",
            reply_markup=backup_keyboard(),
            parse_mode="HTML"
        )

