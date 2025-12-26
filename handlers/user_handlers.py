from aiogram import Router, F
from aiogram.types import Message, ChatJoinRequest, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database import (
    add_user, get_movie_by_code, get_movies_count, 
    get_users_count, get_total_views, is_admin,
    is_subscription_enabled, get_all_channels,
    add_join_request, has_join_request,
    is_premium_user, is_premium_enabled, get_all_premium_plans,
    get_premium_plan, add_premium_request, get_payment_card,
    # Referal funksiyalar
    is_referral_enabled, add_user_with_referral, get_user_referral_balance,
    get_user_referral_count, get_user_referrals, get_referral_bonus,
    get_min_withdrawal, create_withdrawal_request, get_user_withdrawal_history,
    get_referral_history
)
from keyboards import (
    main_menu_keyboard, admin_menu_keyboard, subscription_keyboard,
    user_premium_plans_keyboard, referral_user_keyboard, 
    main_menu_with_referral_keyboard, withdrawal_confirm_keyboard
)
from states import SearchMovie, PremiumPayment, Withdrawal

router = Router()


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
        
        # Tashqi havolalar (Instagram, YouTube, etc.) - tekshirmaslik, faqat ko'rsatish
        if channel.get('is_external_link'):
            continue  # Tashqi havola - o'tkazib yuborish
        
        # So'rovli guruh uchun - database dan so'rov yuborgan yoki yo'qligini tekshirish
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
            print(f"Subscription check error for channel {channel.get('title')}: {e}")
            return False
    
    return True


async def get_not_subscribed_channels(user_id: int, bot) -> list:
    """Foydalanuvchi obuna bo'lmagan kanallar ro'yxatini olish"""
    if not is_subscription_enabled():
        return []
    
    channels = get_all_channels()
    if not channels:
        return []
    
    not_subscribed = []
    
    for channel in channels:
        channel_id = channel['channel_id']
        
        # Tashqi havolalar (Instagram, YouTube, etc.) - har doim ko'rsatish
        if channel.get('is_external_link'):
            not_subscribed.append(channel)  # Har doim ko'rsatish
            continue
        
        # So'rovli guruh uchun - database dan tekshirish
        if channel.get('is_request_group'):
            if not has_join_request(user_id, channel_id):
                not_subscribed.append(channel)
            continue
        
        # Oddiy Telegram kanal uchun tekshirish
        try:
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except Exception as e:
            # Xatolik bo'lsa - obuna emas deb hisoblaymiz
            not_subscribed.append(channel)
    
    return not_subscribed


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    """Start komandasi"""
    await state.clear()
    
    # Deep link tekshirish (referal yoki kino kodi)
    args = message.text.split()
    referred_by = None
    
    if len(args) > 1:
        param = args[1]
        # Referal havola tekshirish (ref_123456 formatda)
        if param.startswith('ref_'):
            try:
                referred_by = int(param.replace('ref_', ''))
                # O'zini o'zi taklif qilmaslik
                if referred_by == message.from_user.id:
                    referred_by = None
            except:
                pass
    
    # Foydalanuvchini database ga qo'shish (referal bilan)
    if is_referral_enabled() and referred_by:
        is_new = add_user_with_referral(
            user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
            referred_by=referred_by
        )
        if is_new and referred_by:
            # Taklif qilgan odamga xabar yuborish
            bonus = get_referral_bonus()
            try:
                await message.bot.send_message(
                    referred_by,
                    f"🎉 <b>Yangi referal!</b>\n\n"
                    f"👤 {message.from_user.full_name} sizning havolangiz orqali qo'shildi!\n"
                    f"💰 Sizning hisobingizga <b>{bonus:,} so'm</b> qo'shildi!",
                    parse_mode="HTML"
                )
            except:
                pass
    else:
        add_user(
            user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )
    
    # Obuna tekshirish
    if not is_admin(message.from_user.id):
        is_subscribed = await check_subscription(message.from_user.id, message.bot)
        if not is_subscribed:
            channels = get_all_channels()
            # To'liq channel ma'lumotlarini yuborish
            channels_data = [{
                'title': ch['title'], 
                'url': ch['url'],
                'invite_link': ch.get('invite_link'),
                'is_request_group': ch.get('is_request_group'),
                'is_external_link': ch.get('is_external_link'),
                'channel_id': ch.get('channel_id'),
                'channel_username': ch.get('channel_username')
            } for ch in channels]
            await message.answer(
                "❗️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
                reply_markup=subscription_keyboard(channels_data)
            )
            return
    
    # Kino kodi bilan deep link
    if len(args) > 1:
        code = args[1]
        if not code.startswith('ref_'):  # Referal emas
            movie = get_movie_by_code(code)
            if movie:
                caption = movie['caption'] if movie['caption'] else f"🎬 {movie['title']}\n\n📥 Kod: {movie['code']}"
                await message.answer_video(
                    video=movie['file_id'],
                    caption=caption
                )
                return
    
    # Admin uchun
    if is_admin(message.from_user.id):
        from database import get_admin_permissions
        from keyboards import admin_menu_keyboard_dynamic
        perms = get_admin_permissions(message.from_user.id)
        if perms and perms.get('is_super'):
            # Super admin - to'liq menyu
            text = "👑 <b>Super Admin Panel</b>\n\n⬇️ Quyidagi tugmalardan foydalaning:"
            await message.answer(text, reply_markup=admin_menu_keyboard(), parse_mode="HTML")
        else:
            # Oddiy admin - huquqlarga ko'ra menyu
            text = "👤 <b>Admin Panel</b>\n\n⬇️ Sizga ruxsat berilgan tugmalar:"
            await message.answer(text, reply_markup=admin_menu_keyboard_dynamic(perms), parse_mode="HTML")
        return
    
    # Oddiy foydalanuvchi uchun
    is_premium = is_premium_user(message.from_user.id)
    premium_enabled = is_premium_enabled()
    referral_enabled = is_referral_enabled()
    
    # Start xabarini database'dan olish
    from database import get_start_message, get_start_media
    
    start_text = get_start_message()
    start_media = get_start_media()
    keyboard = main_menu_with_referral_keyboard(is_premium, premium_enabled, referral_enabled)
    
    try:
        if start_media:
            if start_media['type'] == 'photo':
                await message.answer_photo(
                    photo=start_media['file_id'],
                    caption=start_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:  # animation/gif
                await message.answer_animation(
                    animation=start_media['file_id'],
                    caption=start_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        else:
            await message.answer(
                start_text, 
                reply_markup=keyboard, 
                parse_mode="HTML"
            )
    except Exception as e:
        # Xatolik bo'lsa oddiy matn yuborish
        await message.answer(
            start_text, 
            reply_markup=keyboard, 
            parse_mode="HTML"
        )


@router.message(F.text == "💎 Premium obuna olish")
async def premium_button_handler(message: Message, state: FSMContext):
    """Premium obuna tugmasi"""
    if is_admin(message.from_user.id):
        return
    
    # Premium yoniq emasligini tekshirish
    if not is_premium_enabled():
        await message.answer("❌ Premium obuna hozircha mavjud emas.")
        return
    
    # Foydalanuvchi allaqachon premium ekanligini tekshirish
    if is_premium_user(message.from_user.id):
        await message.answer(
            "💎 Siz allaqachon Premium foydalanuvchisiz!\n\n"
            "Sizda majburiy obuna talab qilinmaydi."
        )
        return
    
    # Tariflarni ko'rsatish
    plans = get_all_premium_plans()
    if not plans:
        await message.answer("❌ Hozircha tariflar mavjud emas.")
        return
    
    card = get_payment_card()
    
    text = """
💎 <b>Premium Obuna</b>

✨ <b>Afzalliklar:</b>
• Majburiy obunalardan ozod
• Reklama xabarlarsiz
• VIP kontent

💳 <b>To'lov kartasi:</b>
<code>{}</code>

📋 Quyidagi tariflardan birini tanlang:
""".format(card if card else "Karta sozlanmagan")
    
    await message.answer(text, reply_markup=user_premium_plans_keyboard(plans), parse_mode="HTML")


@router.callback_query(F.data.startswith("buy_plan_"))
async def buy_plan_callback(callback: CallbackQuery, state: FSMContext):
    """Tarif tanlash"""
    plan_id = int(callback.data.replace("buy_plan_", ""))
    plan = get_premium_plan(plan_id)
    
    if not plan:
        await callback.answer("❌ Tarif topilmadi", show_alert=True)
        return
    
    card = get_payment_card()
    
    text = f"""
💎 <b>{plan['name']}</b>

💰 Narxi: <b>{plan['price']:,} so'm</b>
📅 Muddat: <b>{plan['duration_days']} kun</b>

💳 <b>To'lov kartasi:</b>
<code>{card if card else "Karta sozlanmagan"}</code>

📸 To'lovni amalga oshirib, chek rasmini yuboring:
"""
    
    await state.set_state(PremiumPayment.waiting_for_receipt)
    await state.update_data(plan_id=plan_id)
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(PremiumPayment.waiting_for_receipt, F.photo | F.document)
async def premium_receipt_handler(message: Message, state: FSMContext):
    """Chek qabul qilish"""
    data = await state.get_data()
    plan_id = data.get('plan_id')
    
    if not plan_id:
        await state.clear()
        return
    
    # Fayl ma'lumotlarini olish
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    else:
        await message.answer("❌ Iltimos, rasm yoki fayl yuboring.")
        return
    
    # So'rovni saqlash
    request_id = add_premium_request(message.from_user.id, plan_id, file_id, file_type)
    
    if request_id:
        premium_enabled = is_premium_enabled()
        await message.answer(
            "✅ Chekingiz qabul qilindi!\n\n"
            "⏳ Admin tekshirib, tasdiqlashini kuting.\n"
            "Tasdiqlangandan so'ng Premium aktivlashadi.",
            reply_markup=main_menu_keyboard(False, premium_enabled)
        )
        
        # Adminlarga xabar yuborish
        from database import get_all_admins
        plan = get_premium_plan(plan_id)
        
        for admin in get_all_admins():
            try:
                from keyboards import premium_request_keyboard
                admin_text = f"""
🆕 <b>Yangi Premium so'rov!</b>

👤 Foydalanuvchi: {message.from_user.full_name}
🆔 ID: <code>{message.from_user.id}</code>
📛 Username: @{message.from_user.username if message.from_user.username else "yo'q"}

💎 Tarif: {plan['name']}
💰 Narx: {plan['price']:,} so'm
📅 Muddat: {plan['duration_days']} kun
"""
                if file_type == "photo":
                    await message.bot.send_photo(
                        admin['user_id'],
                        file_id,
                        caption=admin_text,
                        reply_markup=premium_request_keyboard(request_id),
                        parse_mode="HTML"
                    )
                else:
                    await message.bot.send_document(
                        admin['user_id'],
                        file_id,
                        caption=admin_text,
                        reply_markup=premium_request_keyboard(request_id),
                        parse_mode="HTML"
                    )
            except Exception as e:
                print(f"Admin xabar yuborishda xatolik: {e}")
    else:
        await message.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
    
    await state.clear()


@router.callback_query(F.data == "cancel_premium")
async def cancel_premium_callback(callback: CallbackQuery, state: FSMContext):
    """Premium bekor qilish"""
    await state.clear()
    is_premium = is_premium_user(callback.from_user.id)
    premium_enabled = is_premium_enabled()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.message.answer("📌 Kino kodini yuboring:", reply_markup=main_menu_keyboard(is_premium, premium_enabled))


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback, state: FSMContext):
    """Obunani tekshirish"""
    # Haqiqiy obuna tekshirish (Instagram hisobga olinmaydi)
    is_subscribed = await check_subscription(callback.from_user.id, callback.bot)
    
    if is_subscribed:
        # Hammaga obuna bo'lgan
        try:
            await callback.message.delete()
        except:
            pass
        is_premium = is_premium_user(callback.from_user.id)
        premium_enabled = is_premium_enabled()
        await callback.message.answer(
            "✅ Obuna tasdiqlandi! Endi botdan foydalanishingiz mumkin.\n\n"
            "🔍 Kino kodini yoki nomini yuboring:",
            reply_markup=main_menu_keyboard(is_premium, premium_enabled)
        )
    else:
        # Hali obuna bo'lmagan kanallar bor - yangilangan ro'yxatni ko'rsatish
        not_subscribed_channels = await get_not_subscribed_channels(callback.from_user.id, callback.bot)
        
        # Faqat majburiy kanallar sonini hisoblash (Instagram emas)
        required_count = len([ch for ch in not_subscribed_channels if not ch.get('is_external_link')])
        
        channels_data = [{
            'title': ch['title'], 
            'url': ch['url'],
            'invite_link': ch.get('invite_link'),
            'is_request_group': ch.get('is_request_group'),
            'is_external_link': ch.get('is_external_link'),
            'channel_id': ch.get('channel_id'),
            'channel_username': ch.get('channel_username')
        } for ch in not_subscribed_channels]
        
        try:
            await callback.message.edit_text(
                f"❗️ Siz hali {required_count} ta kanalga obuna bo'lmadingiz:",
                reply_markup=subscription_keyboard(channels_data)
            )
        except:
            pass
        await callback.answer("❌ Hali obuna bo'lmagan kanallar bor!", show_alert=True)


@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message):
    """Yordam"""
    text = """
📖 <b>Bot haqida ma'lumot</b>

🎬 Bu bot orqali kinolarni osongina topishingiz mumkin.

<b>Qanday foydalanish:</b>
1️⃣ Kino kodini yuboring (masalan: 123)
2️⃣ Yoki kino nomini yozing

<b>Buyruqlar:</b>
/start - Botni ishga tushirish
/help - Yordam

📞 Savollar bo'lsa admin bilan bog'laning.
"""
    await message.answer(text, parse_mode="HTML")


@router.message(Command("help"))
async def help_command(message: Message):
    """Yordam komandasi"""
    text = """
ℹ️ <b>Bot haqida</b>

🎬 Kino kodini yuboring va kinoni oling!

💎 Premium obuna - majburiy obunasiz foydalaning!
"""
    await message.answer(text, parse_mode="HTML")


# ===== REFERAL TIZIMI HANDLERLARI =====

@router.message(F.text == "💵 Referal - Pul ishlash")
async def referral_menu_handler(message: Message, state: FSMContext):
    """Referal menyusi"""
    if is_admin(message.from_user.id):
        return
    
    if not is_referral_enabled():
        await message.answer("❌ Referal tizimi hozircha faol emas.")
        return
    
    await state.clear()
    
    balance = get_user_referral_balance(message.from_user.id)
    referral_count = get_user_referral_count(message.from_user.id)
    bonus = get_referral_bonus()
    min_withdrawal = get_min_withdrawal()
    
    text = f"""
💵 <b>Referal - Pul ishlash</b>

📊 <b>Sizning statistikangiz:</b>
├ 👥 Taklif qilganlar: <b>{referral_count}</b> ta
├ 💰 Balans: <b>{balance:,} so'm</b>
└ 💵 Har bir referal: <b>{bonus:,} so'm</b>

📝 <b>Qanday ishlaydi?</b>
1. Referal havolangizni do'stlaringizga ulashing
2. Ular bot orqali ro'yxatdan o'tishadi
3. Har bir yangi foydalanuvchi uchun <b>{bonus:,} so'm</b> olasiz!

💳 Minimal pul chiqarish: <b>{min_withdrawal:,} so'm</b>
"""
    
    await message.answer(text, reply_markup=referral_user_keyboard(), parse_mode="HTML")


@router.message(F.text == "🔗 Referal havolam")
async def referral_link_handler(message: Message):
    """Referal havolani ko'rsatish"""
    if is_admin(message.from_user.id):
        return
    
    if not is_referral_enabled():
        await message.answer("❌ Referal tizimi hozircha faol emas.")
        return
    
    from database import get_referral_message
    from keyboards import referral_link_keyboard
    
    bot_info = await message.bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    
    # Admin tomonidan yozilgan xabar
    custom_message = get_referral_message()
    
    text = f"""🔗 <b>Sizning referal havolangiz:</b>

<code>{referral_link}</code>

{custom_message}
"""
    
    await message.answer(text, reply_markup=referral_link_keyboard(referral_link), parse_mode="HTML")


@router.message(F.text == "💰 Hisobim")
async def referral_balance_handler(message: Message):
    """Referal balansni ko'rsatish"""
    if is_admin(message.from_user.id):
        return
    
    if not is_referral_enabled():
        await message.answer("❌ Referal tizimi hozircha faol emas.")
        return
    
    balance = get_user_referral_balance(message.from_user.id)
    referral_count = get_user_referral_count(message.from_user.id)
    bonus = get_referral_bonus()
    
    text = f"""
💰 <b>Sizning hisobingiz</b>

💵 Balans: <b>{balance:,} so'm</b>
👥 Taklif qilganlar: <b>{referral_count}</b> ta
💸 Jami ishlab topgan: <b>{referral_count * bonus:,} so'm</b>

📈 Ko'proq pul ishlash uchun ko'proq do'stlaringizni taklif qiling!
"""
    
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📊 Statistikam")
async def referral_stats_handler(message: Message):
    """Referal statistikasi"""
    if is_admin(message.from_user.id):
        return
    
    if not is_referral_enabled():
        await message.answer("❌ Referal tizimi hozircha faol emas.")
        return
    
    referrals = get_user_referrals(message.from_user.id)
    
    if not referrals:
        text = """
📊 <b>Sizning statistikangiz</b>

👥 Hali hech kimni taklif qilmagansiz.

🔗 Referal havolangizni ulashing va pul ishlab!
"""
    else:
        text = f"📊 <b>Sizning referallaringiz</b>\n\n"
        text += f"👥 Jami: <b>{len(referrals)}</b> ta\n\n"
        
        for i, ref in enumerate(referrals[:10], 1):
            name = ref['full_name'] if ref['full_name'] else "Noma'lum"
            username = f"@{ref['username']}" if ref['username'] else ""
            date = ref['joined_date'][:10] if ref['joined_date'] else ""
            text += f"{i}. {name} {username} - {date}\n"
        
        if len(referrals) > 10:
            text += f"\n... va yana {len(referrals) - 10} ta"
    
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📜 Tarix")
async def referral_history_handler(message: Message):
    """Pul chiqarish tarixi"""
    if is_admin(message.from_user.id):
        return
    
    if not is_referral_enabled():
        await message.answer("❌ Referal tizimi hozircha faol emas.")
        return
    
    history = get_user_withdrawal_history(message.from_user.id)
    
    if not history:
        text = """
📜 <b>Pul chiqarish tarixi</b>

Hali pul chiqarish so'rovi yubormadingiz.
"""
    else:
        text = "📜 <b>Pul chiqarish tarixi</b>\n\n"
        
        status_emoji = {
            'pending': '⏳',
            'approved': '✅',
            'rejected': '❌'
        }
        
        for item in history[:10]:
            emoji = status_emoji.get(item['status'], '❓')
            date = item['created_date'][:10] if item['created_date'] else ""
            text += f"{emoji} {item['amount']:,} so'm - {date}\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "💳 Pul chiqarish")
async def withdrawal_start_handler(message: Message, state: FSMContext):
    """Pul chiqarish boshlash"""
    if is_admin(message.from_user.id):
        return
    
    if not is_referral_enabled():
        await message.answer("❌ Referal tizimi hozircha faol emas.")
        return
    
    balance = get_user_referral_balance(message.from_user.id)
    min_withdrawal = get_min_withdrawal()
    
    if balance < min_withdrawal:
        await message.answer(
            f"❌ <b>Balans yetarli emas!</b>\n\n"
            f"💰 Sizning balans: <b>{balance:,} so'm</b>\n"
            f"💳 Minimal chiqarish: <b>{min_withdrawal:,} so'm</b>\n\n"
            f"📈 Yana <b>{min_withdrawal - balance:,} so'm</b> kerak!",
            parse_mode="HTML"
        )
        return
    
    await state.set_state(Withdrawal.waiting_for_amount)
    await state.update_data(balance=balance)
    
    await message.answer(
        f"💳 <b>Pul chiqarish</b>\n\n"
        f"💰 Sizning balans: <b>{balance:,} so'm</b>\n"
        f"💳 Minimal chiqarish: <b>{min_withdrawal:,} so'm</b>\n\n"
        f"Qancha pul chiqarmoqchisiz? (faqat raqam kiriting)",
        parse_mode="HTML"
    )


@router.message(Withdrawal.waiting_for_amount)
async def withdrawal_amount_handler(message: Message, state: FSMContext):
    """Pul miqdorini qabul qilish"""
    if message.text == "🔙 Asosiy menyu":
        await state.clear()
        is_premium = is_premium_user(message.from_user.id)
        premium_enabled = is_premium_enabled()
        referral_enabled = is_referral_enabled()
        await message.answer(
            "🏠 Asosiy menyu", 
            reply_markup=main_menu_with_referral_keyboard(is_premium, premium_enabled, referral_enabled)
        )
        return
    
    try:
        amount = int(message.text.replace(" ", "").replace(",", ""))
    except:
        await message.answer("❌ Noto'g'ri format! Faqat raqam kiriting:")
        return
    
    data = await state.get_data()
    balance = data.get('balance', 0)
    min_withdrawal = get_min_withdrawal()
    
    if amount < min_withdrawal:
        await message.answer(f"❌ Minimal chiqarish summasi: {min_withdrawal:,} so'm")
        return
    
    if amount > balance:
        await message.answer(f"❌ Balans yetarli emas! Sizda: {balance:,} so'm")
        return
    
    await state.update_data(amount=amount)
    await state.set_state(Withdrawal.waiting_for_card)
    
    await message.answer(
        f"💳 <b>Karta raqamini kiriting</b>\n\n"
        f"💰 Chiqarish summasi: <b>{amount:,} so'm</b>\n\n"
        f"Karta raqamini 16 raqamda kiriting:\n"
        f"Masalan: <code>8600123456789012</code>",
        parse_mode="HTML"
    )


@router.message(Withdrawal.waiting_for_card)
async def withdrawal_card_handler(message: Message, state: FSMContext):
    """Karta raqamini qabul qilish"""
    if message.text == "🔙 Asosiy menyu":
        await state.clear()
        is_premium = is_premium_user(message.from_user.id)
        premium_enabled = is_premium_enabled()
        referral_enabled = is_referral_enabled()
        await message.answer(
            "🏠 Asosiy menyu", 
            reply_markup=main_menu_with_referral_keyboard(is_premium, premium_enabled, referral_enabled)
        )
        return
    
    card = message.text.replace(" ", "").replace("-", "")
    
    if not card.isdigit() or len(card) != 16:
        await message.answer("❌ Noto'g'ri karta raqami! 16 raqam kiriting:")
        return
    
    data = await state.get_data()
    amount = data.get('amount')
    
    await state.update_data(card=card)
    await state.set_state(Withdrawal.confirm)
    
    # Karta raqamini formatlash
    formatted_card = f"{card[:4]} {card[4:8]} {card[8:12]} {card[12:]}"
    
    await message.answer(
        f"✅ <b>Tasdiqlang</b>\n\n"
        f"💰 Summa: <b>{amount:,} so'm</b>\n"
        f"💳 Karta: <code>{formatted_card}</code>\n\n"
        f"So'rovni yuborasizmi?",
        reply_markup=withdrawal_confirm_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_withdrawal")
async def confirm_withdrawal_handler(callback: CallbackQuery, state: FSMContext):
    """Pul chiqarish tasdiqlash"""
    data = await state.get_data()
    amount = data.get('amount')
    card = data.get('card')
    
    if not amount or not card:
        await callback.answer("❌ Xatolik! Qaytadan urinib ko'ring.", show_alert=True)
        await state.clear()
        return
    
    success, msg = create_withdrawal_request(callback.from_user.id, amount, card)
    
    if success:
        await callback.message.edit_text(
            f"✅ <b>So'rov yuborildi!</b>\n\n"
            f"💰 Summa: <b>{amount:,} so'm</b>\n"
            f"💳 Karta: <code>{card[:4]} **** **** {card[12:]}</code>\n\n"
            f"⏳ So'rovingiz ko'rib chiqiladi. Kutib turing!",
            parse_mode="HTML"
        )
        
        # Adminlarga xabar
        from config import ADMINS
        for admin_id in ADMINS:
            try:
                await callback.bot.send_message(
                    admin_id,
                    f"💳 <b>Yangi pul chiqarish so'rovi!</b>\n\n"
                    f"👤 Foydalanuvchi: {callback.from_user.full_name}\n"
                    f"💰 Summa: <b>{amount:,} so'm</b>\n\n"
                    f"📍 Referal boshqaruvi → So'rovlar",
                    parse_mode="HTML"
                )
            except:
                pass
    else:
        await callback.message.edit_text(f"❌ Xatolik: {msg}", parse_mode="HTML")
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_withdrawal")
async def cancel_withdrawal_handler(callback: CallbackQuery, state: FSMContext):
    """Pul chiqarishni bekor qilish"""
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()


@router.message(F.text == "🔙 Asosiy menyu")
async def back_to_main_menu_handler(message: Message, state: FSMContext):
    """Asosiy menyuga qaytish"""
    await state.clear()
    
    if is_admin(message.from_user.id):
        from database import get_admin_permissions
        from keyboards import admin_menu_keyboard_dynamic
        perms = get_admin_permissions(message.from_user.id)
        if perms and perms.get('is_super'):
            text = "👑 <b>Super Admin Panel</b>\n\n⬇️ Quyidagi tugmalardan foydalaning:"
            await message.answer(text, reply_markup=admin_menu_keyboard(), parse_mode="HTML")
        else:
            text = "👤 <b>Admin Panel</b>\n\n⬇️ Sizga ruxsat berilgan tugmalar:"
            await message.answer(text, reply_markup=admin_menu_keyboard_dynamic(perms), parse_mode="HTML")
        return
    
    is_premium = is_premium_user(message.from_user.id)
    premium_enabled = is_premium_enabled()
    referral_enabled = is_referral_enabled()
    
    text = """
🎬 <b>Kino Bot</b>ga xush kelibsiz!

📌 Kino kodini yuboring va kinoni oling!
"""
    
    await message.answer(
        text, 
        reply_markup=main_menu_with_referral_keyboard(is_premium, premium_enabled, referral_enabled), 
        parse_mode="HTML"
    )


# Chat Join Request handler - so'rovlarni database ga saqlash
@router.chat_join_request()
async def chat_join_request_handler(request: ChatJoinRequest):
    """Guruhga qo'shilish so'rovini database ga saqlash"""
    try:
        user_id = request.from_user.id
        channel_id = request.chat.id
        
        # So'rovni database ga saqlash
        add_join_request(user_id, channel_id)
        print(f"Join request saved: user={user_id}, channel={channel_id}")
        
    except Exception as e:
        print(f"Chat join request error: {e}")
