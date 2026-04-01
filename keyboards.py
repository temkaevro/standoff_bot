from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List

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

def get_cancel_inline():
    """Инлайн-кнопка отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])

def get_weapons_keyboard(weapons: List[str], page: int = 0, items_per_page: int = 5):
    """Инлайн-клавиатура для выбора оружия с пагинацией"""
    total_pages = (len(weapons) + items_per_page - 1) // items_per_page
    start = page * items_per_page
    end = start + items_per_page
    current_weapons = weapons[start:end]
    
    buttons = []
    for weapon in current_weapons:
        buttons.append([InlineKeyboardButton(text=weapon, callback_data=f"weapon_{weapon}")])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"weapon_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"weapon_page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_skins_keyboard(skins: List[str], page: int = 0, items_per_page: int = 5):
    """Инлайн-клавиатура для выбора скинов с пагинацией"""
    total_pages = (len(skins) + items_per_page - 1) // items_per_page
    start = page * items_per_page
    end = start + items_per_page
    current_skins = skins[start:end]
    
    buttons = []
    for skin in current_skins:
        buttons.append([InlineKeyboardButton(text=skin, callback_data=f"skin_{skin}")])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"skin_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"skin_page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_stickers_keyboard(stickers: List[str], page: int = 0, items_per_page: int = 5):
    """Инлайн-клавиатура для выбора наклейки с пагинацией"""
    total_pages = (len(stickers) + items_per_page - 1) // items_per_page
    start = page * items_per_page
    end = start + items_per_page
    current_stickers = stickers[start:end]
    
    buttons = []
    for sticker in current_stickers:
        buttons.append([InlineKeyboardButton(text=sticker, callback_data=f"sticker_{sticker}")])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"sticker_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"sticker_page_{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_same_sticker_keyboard():
    """Инлайн-клавиатура: та же наклейка или выбрать другую"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Та же наклейка", callback_data="same_sticker")],
        [InlineKeyboardButton(text="🔄 Другая наклейка", callback_data="different_sticker")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])

def get_confirmation_keyboard():
    """Инлайн-клавиатура подтверждения публикации"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data="confirm")],
        [InlineKeyboardButton(text="✏️ Изменить цену", callback_data="edit_price")],
        [InlineKeyboardButton(text="🔄 Изменить наклейки", callback_data="edit_stickers")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
    ])

def get_listing_actions_keyboard(listing_id: int):
    """Инлайн-клавиатура действий с объявлением"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"edit_price_{listing_id}")],
        [InlineKeyboardButton(text="🔄 Торг", callback_data=f"toggle_bargain_{listing_id}")],
        [InlineKeyboardButton(text="🔄 Обмен", callback_data=f"toggle_trade_{listing_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{listing_id}")]
    ])

def get_buy_listing_keyboard(seller_username: str, listing_id: int):
    """Инлайн-клавиатура для просмотра объявления покупателем"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Купить", callback_data=f"buy_{listing_id}")],
        [InlineKeyboardButton(text="💬 Предложить цену", callback_data=f"offer_{listing_id}")],
        [InlineKeyboardButton(text="📦 Другие скины продавца", callback_data=f"seller_listings_{listing_id}")]
    ])
