from aiogram.fsm.state import StatesGroup, State

class SellStates(StatesGroup):
    """Состояния для процесса продажи"""
    waiting_for_weapon = State()
    waiting_for_skin = State()
    waiting_for_stickers_count = State()
    waiting_for_sticker = State()  # выбор наклейки
    waiting_for_sticker_choice = State()  # такая же или другая
    waiting_for_price_gold = State()
    waiting_for_price_rub = State()
    waiting_for_price_stars = State()
    waiting_for_trade = State()
    waiting_for_bargain = State()
    waiting_for_photo = State()
    waiting_for_confirmation = State()
