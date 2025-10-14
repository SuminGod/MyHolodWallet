# handlers/expense.py
import datetime
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.cancel_handler import cancel_handler
from utils.user_manager import sheets_manager

from keyboards import main_kb, expense_kb

router = Router()

class ExpenseStates(StatesGroup):
    category = State()
    amount = State()

# ========== РАСХОДЫ ==========
@router.message(lambda m: m.text == "📤 Добавить расход")
async def add_expense_start(message: Message, state: FSMContext):
    await state.set_state(ExpenseStates.category)
    await message.answer("На что потратил?", reply_markup=expense_kb)

@router.message(ExpenseStates.category)
async def process_expense_category(message: Message, state: FSMContext):
    if await cancel_handler(message, state):
        return
        
    await state.update_data(category=message.text)
    await state.set_state(ExpenseStates.amount)
    await message.answer("💰 Сколько потратил?")

@router.message(ExpenseStates.amount)
async def process_expense_amount(message: Message, state: FSMContext):
    try:
        user_id = str(message.from_user.id)
        
        data = await state.get_data()
        category = data["category"]
        amount = float(message.text.replace(',', '.'))
        
        today = datetime.date.today().strftime("%d.%m.%Y")
        values = [today, category, amount, ""]
        sheets_manager.append_user_row(sheets_manager.sheet_expense, user_id, values)
        
        await message.answer(f"✅ Расход добавлен: {amount} ₽", reply_markup=main_kb)
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введи нормальную сумму:")

# Обработка кнопки "Назад"
@router.message(lambda m: m.text == "⬅️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_kb)
