from aiogram.fsm.state import StatesGroup, State

class SellStates(StatesGroup):
    """Состояния для процесса продажи"""
    waiting_for_weapon = State()
    waiting_for_skin = State()
    waiting_for_stickers_count = State()
    waiting_for_sticker = State()          # выбор наклейки
    waiting_for_sticker_choice = State()   # та же или другая
    waiting_for_currencies = State()       # выбор валют для цен
    waiting_for_price_input = State()      # ввод конкретной цены
    waiting_for_flags = State()            # выбор обмена/торга
    waiting_for_photo = State()
    waiting_for_confirmation = State()
