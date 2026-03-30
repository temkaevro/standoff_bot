import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import init_db, register_user, user_exists

TOKEN = "8400166396:AAFtMhz6YpKXQS8avIy1GBDeSovSirkjmiQ"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализация БД при старте
init_db()

# Клавиатура
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Продать")],
        [KeyboardButton(text="🔍 Найти / Купить")],
        [KeyboardButton(text="📋 Мои объявления")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    if not user_exists(user_id):
        register_user(user_id, username)
        await message.answer(f"✅ Добро пожаловать, {username or 'пользователь'}! Ты зарегистрирован.")
    else:
        await message.answer("👋 С возвращением! Используй кнопки.")
    await message.answer("Выбери действие:", reply_markup=main_kb)

@dp.message(lambda msg: msg.text == "🛒 Продать")
async def sell_button(message: types.Message):
    await message.answer("🚧 Функция продажи в разработке.")

@dp.message(lambda msg: msg.text == "🔍 Найти / Купить")
async def buy_button(message: types.Message):
    await message.answer("🔍 Функция поиска в разработке.")

@dp.message(lambda msg: msg.text == "📋 Мои объявления")
async def my_listings_button(message: types.Message):
    await message.answer("📋 Функция моих объявлений в разработке.")

@dp.message(lambda msg: msg.text == "❓ Помощь")
async def help_button(message: types.Message):
    await message.answer(
        "❓ Помощь:\n"
        "/start — главное меню\n"
        "/cancel — отменить текущее действие\n"
        "Скоро будут доступны продажа и покупка скинов."
    )

@dp.message(Command("cancel"))
async def cancel_cmd(message: types.Message):
    await message.answer("❌ Отменено.", reply_markup=main_kb)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
