from aiogram.fsm.state import StatesGroup, State

class SellStates(StatesGroup):
    """Состояния для процесса продажи"""
    waiting_for_weapon = State()
    waiting_for_skin = State()
    waiting_for_stickers_count = State()
    waiting_for_sticker_slot = State()          # выбор слота наклейки
    waiting_for_sticker_for_slot = State()      # выбор наклейки для конкретного слота
    waiting_for_currencies = State()
    waiting_for_price_input = State()
    waiting_for_flags = State()
    waiting_for_photo = State()
    waiting_for_confirmation = State()
