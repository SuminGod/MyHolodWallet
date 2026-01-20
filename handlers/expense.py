# handlers/expense.py
import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.cancel_handler import cancel_handler
from utils.user_manager import sheets_manager
from keyboards import main_kb, get_expense_kb, get_work_kb

router = Router()

class ExpenseStates(StatesGroup):
    category = State()
    amount = State()

# --- ЛИЧНЫЕ РАСХОДЫ ---
@router.message(F.text == "📤 Расход")
async def add_personal_expense(message: Message, state: FSMContext):
    await state.set_state(ExpenseStates.category)
    await state.update_data(type="Личное")
    await message.answer("На что потратил (Личное)?", reply_markup=get_expense_kb())

# --- РАБОЧИЕ РАСХОДЫ ---
@router.message(F.text == "🔧 Расход (Работа)")
async def add_work_expense(message: Message, state: FSMContext):
    await state.set_state(ExpenseStates.category)
    await state.update_data(type="Работа")
    # Можно использовать ту же клавиатуру или создать отдельную для работы
    await message.answer("На что потратил (Работа)?", reply_markup=get_expense_kb())

@router.message(ExpenseStates.category)
async def process_exp_cat(message: Message, state: FSMContext):
    if await cancel_handler(message, state): return
    await state.update_data(category=message.text)
    await state.set_state(ExpenseStates.amount)
    await message.answer(f"Сколько потратил на {message.text}?")

@router.message(ExpenseStates.amount)
async def save_expense(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        user_id = str(message.from_user.id)
        today = datetime.date.today().strftime("%d.%m.%Y")
        
        # Таблица Expense: Дата | Тип | Категория | Сумма | Коммент
        values = [today, data['type'], data['category'], amount, ""]
        sheets_manager.append_user_row(sheets_manager.sheet_expense, user_id, values)
        
        kb = main_kb if data['type'] == "Личное" else get_work_kb()
        await message.answer(f"✅ Расход {amount}₽ записан!", reply_markup=kb)
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")
