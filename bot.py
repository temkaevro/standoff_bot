import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8400166396:AAFtMhz6YpKXQS8avIy1GBDeSovSirkjmiQ"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

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
    await message.answer("👋 Бот работает!", reply_markup=main_kb)

@dp.message(lambda msg: msg.text == "🛒 Продать")
async def sell_button(message: types.Message):
    await message.answer("🚧 Функция продажи скоро появится.")

@dp.message(lambda msg: msg.text == "🔍 Найти / Купить")
async def buy_button(message: types.Message):
    await message.answer("🔍 Поиск скоро появится.")

@dp.message(lambda msg: msg.text == "📋 Мои объявления")
async def my_listings_button(message: types.Message):
    await message.answer("📋 Ваши объявления будут здесь.")

@dp.message(lambda msg: msg.text == "❓ Помощь")
async def help_button(message: types.Message):
    await message.answer("❓ /start - меню, /cancel - отмена")

@dp.message(Command("cancel"))
async def cancel_cmd(message: types.Message):
    await message.answer("❌ Отменено.", reply_markup=main_kb)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
