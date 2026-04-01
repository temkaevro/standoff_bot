import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from database import (
    init_db, register_user, user_exists,
    get_weapons, get_skins_by_weapon, get_stickers,
    create_listing, get_user_listings, delete_listing,
    update_listing_price, get_listing_by_id
)
from states import SellStates
from keyboards import (
    get_main_inline_keyboard, get_cancel_inline, get_weapons_keyboard, get_skins_keyboard,
    get_stickers_keyboard, get_same_sticker_keyboard, get_confirmation_keyboard,
    get_listing_actions_keyboard, get_currencies_keyboard, get_flags_keyboard
)

TOKEN = "8400166396:AAFtMhz6YpKXQS8avIy1GBDeSovSirkjmiQ"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация БД
init_db()

# Если база пуста, заполняем
from database import get_weapons
if not get_weapons():
    from seed_full import seed_full
    seed_full()

# ==================== ОСНОВНЫЕ КОМАНДЫ ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or ""
    if not user_exists(user_id):
        register_user(user_id, username)
        await message.answer(f"✅ Добро пожаловать, {username or 'пользователь'}! Ты зарегистрирован.")
    else:
        await message.answer("👋 С возвращением!")
    await message.answer("Выбери действие:", reply_markup=get_main_inline_keyboard())

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено.", reply_markup=get_main_inline_keyboard())

# ==================== ГЛАВНОЕ МЕНЮ (ИНЛАЙН) ====================
@dp.callback_query(F.data.startswith("main_"))
async def main_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_", 1)[1]
    if action == "sell":
        await sell_start(callback.message, state)
    elif action == "buy":
        await callback.message.edit_text("🔍 Функция поиска и покупки скоро появится!")
    elif action == "my_listings":
        await my_listings(callback.message)
    elif action == "help":
        await help_button(callback.message)
    await callback.answer()

# ==================== ПРОДАЖА ====================
async def sell_start(message: types.Message, state: FSMContext):
    await state.clear()
    weapons = get_weapons()
    if not weapons:
        await message.answer("⚠️ Справочник оружия пуст. Обратитесь к администратору.")
        return
    await state.set_state(SellStates.waiting_for_weapon)
    await state.update_data(weapon_page=0)
    await message.answer("🔫 Выбери оружие:", reply_markup=get_weapons_keyboard(weapons, page=0))

# Обработка пагинации и выбора оружия
@dp.callback_query(SellStates.waiting_for_weapon, F.data.startswith("weapon_page_"))
async def weapon_page_callback(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[2])
    await state.update_data(weapon_page=page)
    weapons = get_weapons()
    await callback.message.edit_reply_markup(reply_markup=get_weapons_keyboard(weapons, page=page))
    await callback.answer()

@dp.callback_query(SellStates.waiting_for_weapon, F.data.startswith("weapon_"))
async def weapon_selected(callback: types.CallbackQuery, state: FSMContext):
    weapon = callback.data.split("_", 1)[1]
    await state.update_data(weapon=weapon, skin_page=0)
    skins = get_skins_by_weapon(weapon)
    if not skins:
        await callback.message.edit_text("⚠️ Для этого оружия нет скинов. Выбери другое.")
        await callback.answer()
        return
    await state.set_state(SellStates.waiting_for_skin)
    await callback.message.edit_text(f"Выбрано: {weapon}\n🎨 Выбери скин:", reply_markup=get_skins_keyboard(skins, page=0))
    await callback.answer()

# Обработка пагинации и выбора скинов
@dp.callback_query(SellStates.waiting_for_skin, F.data.startswith("skin_page_"))
async def skin_page_callback(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[2])
    await state.update_data(skin_page=page)
    data = await state.get_data()
    weapon = data["weapon"]
    skins = get_skins_by_weapon(weapon)
    await callback.message.edit_reply_markup(reply_markup=get_skins_keyboard(skins, page=page))
    await callback.answer()

@dp.callback_query(SellStates.waiting_for_skin, F.data.startswith("skin_"))
async def skin_selected(callback: types.CallbackQuery, state: FSMContext):
    skin = callback.data.split("_", 1)[1]
    await state.update_data(skin=skin, stickers=[], current_sticker_index=0)
    await state.set_state(SellStates.waiting_for_stickers_count)
    await callback.message.delete()
    await callback.message.answer("📌 Сколько наклеек на скине? (1-4)\nВведи число:")
    await callback.answer()

# Количество наклеек
@dp.message(SellStates.waiting_for_stickers_count)
async def stickers_count_input(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_inline_keyboard())
        return
    try:
        count = int(message.text)
        if count < 1 or count > 4:
            raise ValueError
    except ValueError:
        await message.answer("Введи число от 1 до 4.")
        return
    await state.update_data(stickers_count=count, current_sticker_index=0)
    await state.set_state(SellStates.waiting_for_sticker)
    await ask_next_sticker(message, state)

async def ask_next_sticker(message: types.Message, state: FSMContext):
    data = await state.get_data()
    count = data.get("stickers_count")
    current = data.get("current_sticker_index", 0)
    stickers_list = data.get("stickers", [])
    if current >= count:
        await state.update_data(stickers=stickers_list)
        # Переходим к выбору валют
        await state.set_state(SellStates.waiting_for_currencies)
        await state.update_data(selected_currencies={"gold": False, "rub": False, "stars": False},
                                prices={"gold": 0, "rub": 0, "stars": 0})
        await message.answer(
            "Выбери валюты, в которых хочешь указать цену. Нажми на кнопку, чтобы включить/выключить.\nПосле выбора нажми 'Готово'.",
            reply_markup=get_currencies_keyboard({"gold": False, "rub": False, "stars": False})
        )
        return
    sticker_num = current + 1
    all_stickers = get_stickers()
    if not all_stickers:
        await message.answer("⚠️ Справочник наклеек пуст. Пропускаем наклейки.")
        await state.update_data(stickers=[])
        await state.set_state(SellStates.waiting_for_currencies)
        await state.update_data(selected_currencies={"gold": False, "rub": False, "stars": False},
                                prices={"gold": 0, "rub": 0, "stars": 0})
        await message.answer(
            "Выбери валюты, в которых хочешь указать цену. Нажми на кнопку, чтобы включить/выключить.\nПосле выбора нажми 'Готово'.",
            reply_markup=get_currencies_keyboard({"gold": False, "rub": False, "stars": False})
        )
        return
    await state.update_data(sticker_page=0)
    await message.answer(f"🎨 Выбери наклейку №{sticker_num} из {count}:", reply_markup=get_stickers_keyboard(all_stickers, page=0))

# Обработка выбора наклейки (пагинация и выбор)
@dp.callback_query(SellStates.waiting_for_sticker, F.data.startswith("sticker_page_"))
async def sticker_page_callback(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[2])
    await state.update_data(sticker_page=page)
    all_stickers = get_stickers()
    await callback.message.edit_reply_markup(reply_markup=get_stickers_keyboard(all_stickers, page=page))
    await callback.answer()

@dp.callback_query(SellStates.waiting_for_sticker, F.data.startswith("sticker_"))
async def sticker_selected(callback: types.CallbackQuery, state: FSMContext):
    sticker = callback.data.split("_", 1)[1]
    data = await state.get_data()
    stickers_list = data.get("stickers", [])
    stickers_list.append(sticker)
    await state.update_data(stickers=stickers_list)
    current = data.get("current_sticker_index", 0)
    count = data.get("stickers_count")
    current += 1
    await state.update_data(current_sticker_index=current)
    if current < count:
        await state.set_state(SellStates.waiting_for_sticker_choice)
        await callback.message.delete()
        await callback.message.answer(
            f"Выбрана наклейка: {sticker}\nСледующая наклейка такая же?",
            reply_markup=get_same_sticker_keyboard()
        )
    else:
        # Все наклейки выбраны, переходим к выбору валют
        await state.update_data(stickers=stickers_list)
        await state.set_state(SellStates.waiting_for_currencies)
        await state.update_data(selected_currencies={"gold": False, "rub": False, "stars": False},
                                prices={"gold": 0, "rub": 0, "stars": 0})
        await callback.message.delete()
        await callback.message.answer(
            "Выбери валюты, в которых хочешь указать цену. Нажми на кнопку, чтобы включить/выключить.\nПосле выбора нажми 'Готово'.",
            reply_markup=get_currencies_keyboard({"gold": False, "rub": False, "stars": False})
        )
    await callback.answer()

# Обработка выбора "та же наклейка" или "другая"
@dp.callback_query(SellStates.waiting_for_sticker_choice, F.data.in_(["same_sticker", "different_sticker"]))
async def sticker_choice(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    count = data.get("stickers_count")
    current = data.get("current_sticker_index", 0)
    stickers_list = data.get("stickers", [])
    if callback.data == "same_sticker":
        last_sticker = stickers_list[-1]
        stickers_list.append(last_sticker)
        await state.update_data(stickers=stickers_list)
        current += 1
        await state.update_data(current_sticker_index=current)
        if current < count:
            # Показать то же сообщение, но удалив старое
            await callback.message.delete()
            await callback.message.answer(
                f"Выбрана наклейка: {last_sticker}\nСледующая наклейка такая же?",
                reply_markup=get_same_sticker_keyboard()
            )
        else:
            await state.update_data(stickers=stickers_list)
            await state.set_state(SellStates.waiting_for_currencies)
            await state.update_data(selected_currencies={"gold": False, "rub": False, "stars": False},
                                    prices={"gold": 0, "rub": 0, "stars": 0})
            await callback.message.delete()
            await callback.message.answer(
                "Выбери валюты, в которых хочешь указать цену. Нажми на кнопку, чтобы включить/выключить.\nПосле выбора нажми 'Готово'.",
                reply_markup=get_currencies_keyboard({"gold": False, "rub": False, "stars": False})
            )
    else:  # different_sticker
        await state.set_state(SellStates.waiting_for_sticker)
        await callback.message.delete()
        await ask_next_sticker(callback.message, state)
    await callback.answer()

# ==================== ВЫБОР ВАЛЮТ ====================
@dp.callback_query(SellStates.waiting_for_currencies, F.data.startswith("toggle_"))
async def toggle_currency(callback: types.CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]  # gold, rub, stars
    data = await state.get_data()
    selected = data.get("selected_currencies", {})
    selected[currency] = not selected.get(currency, False)
    await state.update_data(selected_currencies=selected)
    await callback.message.edit_reply_markup(reply_markup=get_currencies_keyboard(selected))
    await callback.answer()

@dp.callback_query(SellStates.waiting_for_currencies, F.data == "currencies_done")
async def currencies_done(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_currencies", {})
    if not any(selected.values()):
        await callback.answer("❌ Выбери хотя бы одну валюту!", show_alert=True)
        return
    currencies_to_ask = [c for c, v in selected.items() if v]
    await state.update_data(currencies_to_ask=currencies_to_ask, current_currency_index=0)
    await ask_next_price(callback.message, state)
    await callback.answer()

async def ask_next_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    currencies = data.get("currencies_to_ask", [])
    index = data.get("current_currency_index", 0)
    if index >= len(currencies):
        # Все цены собраны, переходим к флагам
        await state.set_state(SellStates.waiting_for_flags)
        await state.update_data(trade=True, bargain=True)
        await message.answer("Настрой опции продажи:", reply_markup=get_flags_keyboard(True, True))
        return
    
    currency = currencies[index]
    await state.update_data(current_currency=currency)
    await state.set_state(SellStates.waiting_for_price_input)
    currency_names = {"gold": "💰 Голда", "rub": "💵 Рубли", "stars": "⭐ Stars"}
    await message.answer(f"Введи цену в {currency_names[currency]} (целое число, 0 если не продаётся):")

@dp.message(SellStates.waiting_for_price_input)
async def price_input_handler(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_inline_keyboard())
        return
    try:
        price = int(message.text)
        if price < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи целое неотрицательное число.")
        return
    
    data = await state.get_data()
    currency = data.get("current_currency")
    prices = data.get("prices", {})
    prices[currency] = price
    await state.update_data(prices=prices)
    
    # Переходим к следующей валюте
    index = data.get("current_currency_index", 0) + 1
    await state.update_data(current_currency_index=index)
    await ask_next_price(message, state)

# ==================== ВЫБОР ФЛАГОВ (ОБМЕН/ТОРГ) ====================
@dp.callback_query(SellStates.waiting_for_flags, F.data == "toggle_trade")
async def toggle_trade(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    trade = not data.get("trade", True)
    bargain = data.get("bargain", True)
    await state.update_data(trade=trade)
    await callback.message.edit_reply_markup(reply_markup=get_flags_keyboard(trade, bargain))
    await callback.answer()

@dp.callback_query(SellStates.waiting_for_flags, F.data == "toggle_bargain")
async def toggle_bargain(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    trade = data.get("trade", True)
    bargain = not data.get("bargain", True)
    await state.update_data(bargain=bargain)
    await callback.message.edit_reply_markup(reply_markup=get_flags_keyboard(trade, bargain))
    await callback.answer()

@dp.callback_query(SellStates.waiting_for_flags, F.data == "flags_done")
async def flags_done(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SellStates.waiting_for_photo)
    await callback.message.delete()
    await callback.message.answer("📸 Отправь скриншот скина (одно фото):")
    await callback.answer()

# ==================== ПОЛУЧЕНИЕ ФОТО ====================
@dp.message(SellStates.waiting_for_photo, F.photo)
async def photo_received(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    await state.update_data(photo_file_id=file_id)
    data = await state.get_data()
    
    weapon = data.get("weapon")
    skin = data.get("skin")
    stickers = data.get("stickers", [])
    prices = data.get("prices", {})
    price_gold = prices.get("gold", 0)
    price_rub = prices.get("rub", 0)
    price_stars = prices.get("stars", 0)
    trade = data.get("trade", True)
    bargain = data.get("bargain", True)
    
    sticker_text = "\n".join([f"• {s}" for s in stickers]) if stickers else "Нет наклеек"
    price_text = []
    if price_gold > 0:
        price_text.append(f"💰 Голда: {price_gold}")
    if price_rub > 0:
        price_text.append(f"💵 Рубли: {price_rub}")
    if price_stars > 0:
        price_text.append(f"⭐ Stars: {price_stars}")
    price_str = "\n".join(price_text) if price_text else "❌ Нет цен!"
    
    await message.answer_photo(
        photo=file_id,
        caption=f"📋 Проверь данные:\n\n"
                f"🔫 Оружие: {weapon}\n"
                f"🎨 Скин: {skin}\n"
                f"📌 Наклейки:\n{sticker_text}\n\n"
                f"{price_str}\n\n"
                f"🔄 Обмен: {'Да' if trade else 'Нет'}\n"
                f"💬 Торг: {'Да' if bargain else 'Нет'}",
        reply_markup=get_confirmation_keyboard()
    )
    await state.set_state(SellStates.waiting_for_confirmation)

@dp.callback_query(SellStates.waiting_for_confirmation)
async def confirmation_callback(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data
    if action == "confirm":
        data = await state.get_data()
        prices = data.get("prices", {})
        listing_id = create_listing(
            user_id=callback.from_user.id,
            weapon_name=data["weapon"],
            skin_name=data["skin"],
            stickers=data.get("stickers", []),
            price_gold=prices.get("gold", 0),
            price_rub=prices.get("rub", 0),
            price_stars=prices.get("stars", 0),
            trade=data["trade"],
            bargain=data["bargain"],
            photo_file_id=data["photo_file_id"]
        )
        await callback.message.edit_caption(caption=f"✅ Объявление опубликовано! ID: {listing_id}")
        await state.clear()
        await callback.message.answer("Выбери действие:", reply_markup=get_main_inline_keyboard())
    elif action == "edit_price":
        # Для простоты пока оставим старую логику редактирования цен
        await state.set_state("waiting_for_edit_price_gold")
        await callback.message.delete()
        await callback.message.answer("💵 Введи новую цену в Голде (или 0):")
    elif action == "edit_stickers":
        await state.update_data(stickers=[], current_sticker_index=0)
        await state.set_state(SellStates.waiting_for_stickers_count)
        await callback.message.delete()
        await callback.message.answer("📌 Сколько наклеек на скине? (1-4)")
    elif action == "cancel":
        await state.clear()
        await callback.message.edit_caption(caption="❌ Публикация отменена.")
        await callback.message.answer("Выбери действие:", reply_markup=get_main_inline_keyboard())
    await callback.answer()

# ==================== МОИ ОБЪЯВЛЕНИЯ ====================
async def my_listings(message: types.Message):
    listings = get_user_listings(message.from_user.id)
    if not listings:
        await message.answer("📭 У тебя нет активных объявлений.")
        return
    for listing in listings[:5]:
        sticker_text = "\n".join([f"• {s}" for s in listing["stickers"]]) if listing["stickers"] else "Нет наклеек"
        price_text = []
        if listing["price_gold"] > 0:
            price_text.append(f"💰 Голда: {listing['price_gold']}")
        if listing["price_rub"] > 0:
            price_text.append(f"💵 Рубли: {listing['price_rub']}")
        if listing["price_stars"] > 0:
            price_text.append(f"⭐ Stars: {listing['price_stars']}")
        await message.answer_photo(
            photo=listing["photo_file_id"],
            caption=f"🔫 {listing['weapon_name']} {listing['skin_name']}\n"
                    f"📌 Наклейки:\n{sticker_text}\n\n"
                    f"{chr(10).join(price_text)}\n"
                    f"🔄 Обмен: {'Да' if listing['trade'] else 'Нет'}\n"
                    f"💬 Торг: {'Да' if listing['bargain'] else 'Нет'}",
            reply_markup=get_listing_actions_keyboard(listing["id"])
        )
    if len(listings) > 5:
        await message.answer(f"📊 Всего объявлений: {len(listings)}. Показаны первые 5.")

@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def delete_listing_callback(callback: types.CallbackQuery):
    listing_id = int(callback.data.split("_")[1])
    delete_listing(listing_id)
    await callback.message.edit_caption(caption="🗑️ Объявление удалено.")
    await callback.answer()

# Редактирование цен (упрощённо, без изменения на новую систему)
@dp.callback_query(lambda c: c.data.startswith("edit_price_"))
async def edit_price_callback(callback: types.CallbackQuery, state: FSMContext):
    listing_id = int(callback.data.split("_")[2])
    await state.update_data(edit_listing_id=listing_id)
    await state.set_state("waiting_for_edit_price_gold")
    await callback.message.delete()
    await callback.message.answer("💵 Введи новую цену в Голде (или 0):")
    await callback.answer()

@dp.message(StateFilter("waiting_for_edit_price_gold"))
async def edit_price_gold_handler(message: types.Message, state: FSMContext):
    try:
        price_gold = int(message.text)
        await state.update_data(edit_price_gold=price_gold)
        await state.set_state("waiting_for_edit_price_rub")
        await message.answer("💵 Введи цену в рублях (или 0):")
    except ValueError:
        await message.answer("Введи число.")

@dp.message(StateFilter("waiting_for_edit_price_rub"))
async def edit_price_rub_handler(message: types.Message, state: FSMContext):
    try:
        price_rub = int(message.text)
        await state.update_data(edit_price_rub=price_rub)
        await state.set_state("waiting_for_edit_price_stars")
        await message.answer("💵 Введи цену в Stars (или 0):")
    except ValueError:
        await message.answer("Введи число.")

@dp.message(StateFilter("waiting_for_edit_price_stars"))
async def edit_price_stars_handler(message: types.Message, state: FSMContext):
    try:
        price_stars = int(message.text)
        data = await state.get_data()
        listing_id = data.get("edit_listing_id")
        update_listing_price(listing_id, data.get("edit_price_gold"), data.get("edit_price_rub"), price_stars)
        await message.answer("✅ Цена обновлена.", reply_markup=get_main_inline_keyboard())
        await state.clear()
    except ValueError:
        await message.answer("Введи число.")

# ==================== ПОМОЩЬ ====================
async def help_button(message: types.Message):
    await message.answer(
        "❓ Помощь:\n"
        "/start — главное меню\n"
        "/cancel — отменить текущее действие\n"
        "🛒 Продать — создать объявление\n"
        "📋 Мои объявления — управлять своими объявлениями\n"
        "🔍 Найти / Купить — поиск скинов (в разработке)\n\n"
        "По всем вопросам пишите @temkaevro",
        reply_markup=get_main_inline_keyboard()
    )

# ==================== ЗАПУСК ====================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
