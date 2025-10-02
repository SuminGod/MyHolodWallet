# handlers/base.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from keyboards import main_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("💼 Учет финансов холодильников", reply_markup=main_kb)

# УДАЛИ ЭТУ ФУНКЦИЮ ПОЛНОСТЬЮ, ЕСЛИ ОНА ЕСТЬ:
# @router.message()
# async def handle_unknown(message: Message):
#     await message.answer("🤔 Не понял команду. Используй кнопки меню ↓", reply_markup=main_kb)