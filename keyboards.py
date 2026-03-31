from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """Главная клавиатура с кнопками"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Продать")],
            [KeyboardButton(text="🔍 Найти / Купить")],
            [KeyboardButton(text="📋 Мои объявления")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def get_stickers_count_keyboard():
    """Клавиатура выбора количества наклеек (1-4)"""
    buttons = [[KeyboardButton(text=str(i))] for i in range(1, 5)]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_same_sticker_keyboard():
    """Клавиатура: та же наклейка или выбрать другую"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Та же наклейка")],
            [KeyboardButton(text="🔄 Другая наклейка")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def get_confirmation_keyboard():
    """Клавиатура подтверждения публикации"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Опубликовать", callback_data="confirm")],
            [InlineKeyboardButton(text="✏️ Изменить цену", callback_data="edit_price")],
            [InlineKeyboardButton(text="🔄 Изменить наклейки", callback_data="edit_stickers")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
        ]
    )

def get_listing_actions_keyboard(listing_id: int):
    """Клавиатура действий с объявлением (для Моих объявлений)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"edit_price_{listing_id}")],
            [InlineKeyboardButton(text="🔄 Торг", callback_data=f"toggle_bargain_{listing_id}")],
            [InlineKeyboardButton(text="🔄 Обмен", callback_data=f"toggle_trade_{listing_id}")],
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{listing_id}")]
        ]
    )

def get_buy_listing_keyboard(seller_username: str, listing_id: int):
    """Клавиатура для просмотра объявления покупателем"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Купить", callback_data=f"buy_{listing_id}")],
            [InlineKeyboardButton(text="💬 Предложить цену", callback_data=f"offer_{listing_id}")],
            [InlineKeyboardButton(text="📦 Другие скины продавца", callback_data=f"seller_listings_{listing_id}")]
        ]
    )
