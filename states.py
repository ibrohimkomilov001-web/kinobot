from aiogram.fsm.state import State, StatesGroup


class AddMovie(StatesGroup):
    """Kino qo'shish holatlari"""
    waiting_for_video = State()      # 1. Kinoni yuborish
    waiting_for_title = State()      # 2. Film nomini kiritish
    waiting_for_genre = State()      # 3. Film janrini kiritish
    waiting_for_code = State()       # 4. Kino kodini kiritish


class DeleteMovie(StatesGroup):
    """Kino o'chirish holatlari"""
    waiting_for_code = State()


class SearchMovie(StatesGroup):
    """Kino qidirish holatlari"""
    waiting_for_query = State()


class Broadcast(StatesGroup):
    """Reklama yuborish holatlari"""
    choosing_type = State()           # Xabar turini tanlash
    waiting_for_message = State()     # Oddiy xabar
    waiting_for_media = State()       # Rasm/Video yuklash
    waiting_for_caption = State()     # Rasm/Video uchun matn
    waiting_for_button_text = State() # Tugma matni
    waiting_for_button_url = State()  # Tugma havolasi
    adding_more_buttons = State()     # Qo'shimcha tugma qo'shish
    confirm = State()                 # Tasdiqlash


class AddChannel(StatesGroup):
    """Kanal qo'shish holatlari"""
    waiting_for_channel = State()


class AddChannelLink(StatesGroup):
    """Havola orqali kanal qo'shish"""
    waiting_for_url = State()


class AddRequestGroup(StatesGroup):
    """So'rovli guruh qo'shish"""
    waiting_for_group = State()
    waiting_for_invite_link = State()


class SetBaseChannel(StatesGroup):
    """Baza kanal sozlash"""
    waiting_for_channel = State()


class EditSubscriptionMessage(StatesGroup):
    """Obuna xabarini tahrirlash"""
    waiting_for_message = State()


class AddPremiumPlan(StatesGroup):
    """Premium tarif qo'shish"""
    waiting_for_name = State()
    waiting_for_duration = State()
    waiting_for_price = State()
    waiting_for_description = State()


class PremiumPayment(StatesGroup):
    """Premium to'lov"""
    waiting_for_plan = State()
    waiting_for_receipt = State()


class SetPaymentCard(StatesGroup):
    """To'lov kartasini sozlash"""
    waiting_for_card = State()
    waiting_for_message = State()


class AddAdmin(StatesGroup):
    """Admin qo'shish"""
    waiting_for_user_id = State()


class RemoveAdmin(StatesGroup):
    """Admin o'chirish"""
    waiting_for_user_id = State()


class SetReferralBonus(StatesGroup):
    """Referal bonus summasini belgilash"""
    waiting_for_amount = State()


class SetMinWithdrawal(StatesGroup):
    """Minimal pul chiqarish summasini belgilash"""
    waiting_for_amount = State()


class Withdrawal(StatesGroup):
    """Pul chiqarish"""
    waiting_for_amount = State()
    waiting_for_card = State()
    confirm = State()


class EditReferralMessage(StatesGroup):
    """Referal xabarini tahrirlash"""
    waiting_for_message = State()


class EditStartMessage(StatesGroup):
    """Start xabarini tahrirlash"""
    waiting_for_content = State()  # Matn, rasm yoki gif


class EditBotName(StatesGroup):
    """Bot nomini tahrirlash"""
    waiting_for_name = State()
