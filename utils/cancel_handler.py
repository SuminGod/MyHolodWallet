# utils/cancel_handler.py
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from keyboards import main_kb

async def cancel_handler(message: Message, state: FSMContext) -> bool:
    """Универсальный обработчик кнопки 'Назад'"""
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_kb)
        return True
    return False