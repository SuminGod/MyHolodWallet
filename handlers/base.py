# handlers/base.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import F

from keyboards import main_kb
from utils.user_manager import sheets_manager

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    
    if sheets_manager.is_user_allowed(user_id):
        await message.answer("💼 Учет финансов холодильников", reply_markup=main_kb)
    else:
        await message.answer(
            "🔒 Бот доступен только по приглашению.\n"
            "Обратись к администратору для получения доступа.\n\n"
            f"Твой ID: {user_id}"
        )

# Мидлварь для проверки доступа ко всем сообщениям
@router.message(F.chat.type == "private")
async def check_access_middleware(message: Message):
    user_id = str(message.from_user.id)
    if not sheets_manager.is_user_allowed(user_id):
        await message.answer("❌ Доступ запрещен. Обратись к администратору.")
        return
