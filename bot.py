import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove

from database import (
    init_db, register_user, user_exists,
    get_weapons, get_skins_by_weapon, get_stickers,
    create_listing, get_user_listings, delete_listing,
    update_listing_price, update_listing_flags, get_listing_by_id,
    get_active_listings_by_skin
)
from states import SellStates
from keyboards import (
    get_main_keyboard, get_cancel_keyboard, get_stickers_count_keyboard,
    get_same_sticker_keyboard, get_confirmation_keyboard,
    get_listing_actions_keyboard, get_buy_listing_keyboard
)

TOKEN = "8400166396:AAFtMhz6YpKXQS8avIy1GBDeSovSirkjmiQ"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация БД
init_db()

# Временные данные для процесса продажи
user_data = {}

# === Главное меню ===
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
    await message.answer("Выбери действие:", reply_markup=get_main_keyboard())

@dp.message(lambda msg: msg.text == "❌ Отмена", StateFilter("*"))
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Действие отменено.", reply_markup=get_main_keyboard())

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено.", reply_markup=get_main_keyboard())

@dp.message(lambda msg: msg.text == "🛒 Продать")
async def sell_start(message: types.Message, state: FSMContext):
    await state.set_state(SellStates.waiting_for_weapon)
    weapons = get_weapons()
    if not weapons:
        await message.answer("⚠️ Справочник оружия пуст. Обратитесь к администратору.")
        await state.clear()
        return
    
    buttons = [[types.KeyboardButton(text=w)] for w in weapons]
    buttons.append([types.KeyboardButton(text="❌ Отмена")])
    kb = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer("🔫 Выбери оружие:", reply_markup=kb)

@dp.message(SellStates.waiting_for_weapon)
async def sell_weapon(message: types.Message, state: FSMContext):
    weapon = message.text
    if weapon == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_keyboard())
        return
    
    weapons = get_weapons()
    if weapon not in weapons:
        await message.answer("Пожалуйста, выбери оружие из списка.")
        return
    
    await state.update_data(weapon=weapon)
    skins = get_skins_by_weapon(weapon)
    if not skins:
        await message.answer("⚠️ Для этого оружия нет скинов.")
        await state.clear()
        return
    
    buttons = [[types.KeyboardButton(text=s)] for s in skins]
    buttons.append([types.KeyboardButton(text="❌ Отмена")])
    kb = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await state.set_state(SellStates.waiting_for_skin)
    await message.answer(f"Выбрано: {weapon}\n🎨 Выбери скин:", reply_markup=kb)

@dp.message(SellStates.waiting_for_skin)
async def sell_skin(message: types.Message, state: FSMContext):
    skin = message.text
    if skin == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_keyboard())
        return
    
    data = await state.get_data()
    weapon = data.get("weapon")
    skins = get_skins_by_weapon(weapon)
    if skin not in skins:
        await message.answer("Пожалуйста, выбери скин из списка.")
        return
    
    await state.update_data(skin=skin, stickers=[])
    await state.set_state(SellStates.waiting_for_stickers_count)
    await message.answer(f"Выбрано: {weapon} {skin}\n📌 Сколько наклеек на скине? (1-4)", reply_markup=get_stickers_count_keyboard())

@dp.message(SellStates.waiting_for_stickers_count)
async def sell_stickers_count(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_keyboard())
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
        # Все наклейки выбраны
        await state.update_data(stickers=stickers_list)
        await state.set_state(SellStates.waiting_for_price_gold)
        await message.answer("💵 Введи цену в Голде (или 0, если не продаётся за Голду):", reply_markup=get_cancel_keyboard())
        return
    
    sticker_num = current + 1
    # Показываем список наклеек
    stickers = get_stickers()
    if not stickers:
        await message.answer("⚠️ Справочник наклеек пуст. Пропускаем наклейки.")
        await state.update_data(stickers=[])
        await state.set_state(SellStates.waiting_for_price_gold)
        await message.answer("💵 Введи цену в Голде (или 0):")
        return
    
    buttons = [[types.KeyboardButton(text=s)] for s in stickers[:50]]  # ограничим для удобства
    buttons.append([types.KeyboardButton(text="❌ Отмена")])
    kb = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer(f"🎨 Выбери наклейку №{sticker_num} из {count}:", reply_markup=kb)

@dp.message(SellStates.waiting_for_sticker)
async def sell_sticker(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_keyboard())
        return
    
    sticker = message.text
    stickers = get_stickers()
    if sticker not in stickers:
        await message.answer("Пожалуйста, выбери наклейку из списка.")
        return
    
    data = await state.get_data()
    stickers_list = data.get("stickers", [])
    stickers_list.append(sticker)
    await state.update_data(stickers=stickers_list)
    
    current = data.get("current_sticker_index", 0)
    count = data.get("stickers_count")
    current += 1
    await state.update_data(current_sticker_index=current)
    
    if current < count:
        # Спрашиваем, та же наклейка или другая
        await state.set_state(SellStates.waiting_for_sticker_choice)
        await message.answer("Следующая наклейка такая же?", reply_markup=get_same_sticker_keyboard())
    else:
        # Все наклейки выбраны
        await state.update_data(stickers=stickers_list)
        await state.set_state(SellStates.waiting_for_price_gold)
        await message.answer("💵 Введи цену в Голде (или 0):", reply_markup=get_cancel_keyboard())

@dp.message(SellStates.waiting_for_sticker_choice)
async def sell_sticker_choice(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_keyboard())
        return
    
    data = await state.get_data()
    count = data.get("stickers_count")
    current = data.get("current_sticker_index", 0)
    stickers_list = data.get("stickers", [])
    
    if message.text == "✅ Та же наклейка":
        # Добавляем ту же наклейку
        last_sticker = stickers_list[-1]
        stickers_list.append(last_sticker)
        await state.update_data(stickers=stickers_list)
        current += 1
        await state.update_data(current_sticker_index=current)
        
        if current < count:
            await state.set_state(SellStates.waiting_for_sticker_choice)
            await message.answer("Следующая наклейка такая же?", reply_markup=get_same_sticker_keyboard())
        else:
            await state.set_state(SellStates.waiting_for_price_gold)
            await message.answer("💵 Введи цену в Голде (или 0):", reply_markup=get_cancel_keyboard())
    elif message.text == "🔄 Другая наклейка":
        await state.set_state(SellStates.waiting_for_sticker)
        await ask_next_sticker(message, state)
    else:
        await message.answer("Выбери вариант из меню.")

@dp.message(SellStates.waiting_for_price_gold)
async def sell_price_gold(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_keyboard())
        return
    
    try:
        price_gold = int(message.text)
        if price_gold < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи целое число (0 или больше).")
        return
    
    await state.update_data(price_gold=price_gold)
    await state.set_state(SellStates.waiting_for_price_rub)
    await message.answer("💵 Введи цену в рублях (или 0):", reply_markup=get_cancel_keyboard())

@dp.message(SellStates.waiting_for_price_rub)
async def sell_price_rub(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_keyboard())
        return
    
    try:
        price_rub = int(message.text)
        if price_rub < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи целое число (0 или больше).")
        return
    
    await state.update_data(price_rub=price_rub)
    await state.set_state(SellStates.waiting_for_price_stars)
    await message.answer("💵 Введи цену в Telegram Stars (или 0):", reply_markup=get_cancel_keyboard())

@dp.message(SellStates.waiting_for_price_stars)
async def sell_price_stars(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_keyboard())
        return
    
    try:
        price_stars = int(message.text)
        if price_stars < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи целое число (0 или больше).")
        return
    
    data = await state.get_data()
    if data.get("price_gold") == 0 and price_rub == 0 and price_stars == 0:
        await message.answer("❌ Нужно указать хотя бы одну ненулевую цену.")
        return
    
    await state.update_data(price_stars=price_stars)
    await state.set_state(SellStates.waiting_for_trade)
    await message.answer("🔄 Обмен? (Да/Нет):", reply_markup=get_cancel_keyboard())

@dp.message(SellStates.waiting_for_trade)
async def sell_trade(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_keyboard())
        return
    
    text = message.text.lower()
    if text in ["да", "yes", "д", "y"]:
        trade = True
    elif text in ["нет", "no", "н", "n"]:
        trade = False
    else:
        await message.answer("Напиши 'Да' или 'Нет'")
        return
    
    await state.update_data(trade=trade)
    await state.set_state(SellStates.waiting_for_bargain)
    await message.answer("💬 Торг? (Да/Нет):", reply_markup=get_cancel_keyboard())

@dp.message(SellStates.waiting_for_bargain)
async def sell_bargain(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_keyboard())
        return
    
    text = message.text.lower()
    if text in ["да", "yes", "д", "y"]:
        bargain = True
    elif text in ["нет", "no", "н", "n"]:
        bargain = False
    else:
        await message.answer("Напиши 'Да' или 'Нет'")
        return
    
    await state.update_data(bargain=bargain)
    await state.set_state(SellStates.waiting_for_photo)
    await message.answer("📸 Отправь скриншот скина (одно фото):", reply_markup=get_cancel_keyboard())

@dp.message(SellStates.waiting_for_photo, F.photo)
async def sell_photo(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Продажа отменена.", reply_markup=get_main_keyboard())
        return
    
    photo = message.photo[-1]
    file_id = photo.file_id
    
    await state.update_data(photo_file_id=file_id)
    
    data = await state.get_data()
    weapon = data.get("weapon")
    skin = data.get("skin")
    stickers = data.get("stickers", [])
    price_gold = data.get("price_gold")
    price_rub = data.get("price_rub")
    price_stars = data.get("price_stars")
    trade = data.get("trade")
    bargain = data.get("bargain")
    
    # Формируем текст для подтверждения
    sticker_text = "\n".join([f"• {s}" for s in stickers]) if stickers else "Нет наклеек"
    price_text = []
    if price_gold > 0:
        price_text.append(f"💰 Голда: {price_gold}")
    if price_rub > 0:
        price_text.append(f"💵 Рубли: {price_rub}")
    if price_stars > 0:
        price_text.append(f"⭐ Telegram Stars: {price_stars}")
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
async def sell_confirmation(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data
    
    if action == "confirm":
        data = await state.get_data()
        listing_id = create_listing(
            user_id=callback.from_user.id,
            weapon_name=data["weapon"],
            skin_name=data["skin"],
            stickers=data.get("stickers", []),
            price_gold=data["price_gold"],
            price_rub=data["price_rub"],
            price_stars=data["price_stars"],
            trade=data["trade"],
            bargain=data["bargain"],
            photo_file_id=data["photo_file_id"]
        )
        await callback.message.edit_caption(caption=f"✅ Объявление опубликовано! ID: {listing_id}")
        await state.clear()
        await callback.message.answer("Выбери действие:", reply_markup=get_main_keyboard())
    elif action == "edit_price":
        await state.set_state(SellStates.waiting_for_price_gold)
        await callback.message.answer("💵 Введи новую цену в Голде (или 0):", reply_markup=get_cancel_keyboard())
        await callback.message.delete()
    elif action == "edit_stickers":
        await state.update_data(stickers=[], current_sticker_index=0)
        await state.set_state(SellStates.waiting_for_stickers_count)
        await callback.message.answer("📌 Сколько наклеек на скине? (1-4)", reply_markup=get_stickers_count_keyboard())
        await callback.message.delete()
    elif action == "cancel":
        await state.clear()
        await callback.message.edit_caption(caption="❌ Публикация отменена.")
        await callback.message.answer("Выбери действие:", reply_markup=get_main_keyboard())
    
    await callback.answer()

# === Мои объявления ===
@dp.message(lambda msg: msg.text == "📋 Мои объявления")
async def my_listings(message: types.Message):
    listings = get_user_listings(message.from_user.id)
    if not listings:
        await message.answer("📭 У тебя нет активных объявлений.")
        return
    
    for listing in listings[:5]:  # покажем первые 5
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

@dp.callback_query(lambda c: c.data.startswith("edit_price_"))
async def edit_price_callback(callback: types.CallbackQuery, state: FSMContext):
    listing_id = int(callback.data.split("_")[2])
    await state.update_data(edit_listing_id=listing_id)
    await state.set_state("waiting_for_edit_price")
    await callback.message.answer("💵 Введи новую цену в Голде (или 0):", reply_markup=get_cancel_keyboard())
    await callback.answer()

@dp.message(StateFilter("waiting_for_edit_price"))
async def edit_price_handler(message: types.Message, state: FSMContext):
    try:
        price_gold = int(message.text)
        # упростим: запросим все три цены
        await state.update_data(edit_price_gold=price_gold)
        await message.answer("💵 Введи цену в рублях (или 0):")
        await state.set_state("waiting_for_edit_price_rub")
    except ValueError:
        await message.answer("Введи число.")

@dp.message(StateFilter("waiting_for_edit_price_rub"))
async def edit_price_rub_handler(message: types.Message, state: FSMContext):
    try:
        price_rub = int(message.text)
        await state.update_data(edit_price_rub=price_rub)
        await message.answer("💵 Введи цену в Stars (или 0):")
        await state.set_state("waiting_for_edit_price_stars")
    except ValueError:
        await message.answer("Введи число.")

@dp.message(StateFilter("waiting_for_edit_price_stars"))
async def edit_price_stars_handler(message: types.Message, state: FSMContext):
    try:
        price_stars = int(message.text)
        data = await state.get_data()
        listing_id = data.get("edit_listing_id")
        update_listing_price(listing_id, data.get("edit_price_gold"), data.get("edit_price_rub"), price_stars)
        await message.answer("✅ Цена обновлена.", reply_markup=get_main_keyboard())
        await state.clear()
    except ValueError:
        await message.answer("Введи число.")

# === Помощь ===
@dp.message(lambda msg: msg.text == "❓ Помощь")
async def help_button(message: types.Message):
    await message.answer(
        "❓ Помощь:\n"
        "/start — главное меню\n"
        "/cancel — отменить текущее действие\n"
        "🛒 Продать — создать объявление\n"
        "📋 Мои объявления — управлять своими объявлениями\n"
        "🔍 Найти / Купить — поиск скинов (в разработке)\n\n"
        "По всем вопросам пишите @temkaevro"
    )

# === Поиск (пока заглушка) ===
@dp.message(lambda msg: msg.text == "🔍 Найти / Купить")
async def buy_start(message: types.Message):
    await message.answer("🔍 Функция поиска и покупки скоро появится!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
