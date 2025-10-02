# handlers/expense.py
import datetime
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import gspread
from utils.cancel_handler import cancel_handler

from keyboards import main_kb, expense_kb
from config import GSHEET_NAME, GSHEET_CREDS_JSON

router = Router()

# Подключение к Google Sheets
gc = gspread.service_account(filename=GSHEET_CREDS_JSON)
sheet_expense = gc.open(GSHEET_NAME).worksheet("Расходы")

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
        data = await state.get_data()
        category = data["category"]
        amount = float(message.text.replace(',', '.'))
        
        today = datetime.date.today().strftime("%d.%m.%Y")
        values = [today, category, amount, ""]
        sheet_expense.append_row(values)
        
        await message.answer(f"✅ Расход добавлен: {amount} ₽", reply_markup=main_kb)
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введи нормальную сумму:")
        # ОБРАБОТКА ЛЮБЫХ НЕОБРАБОТАННЫХ СООБЩЕНИЙ

    # Обработка кнопки "Назад" из любого состояния
@router.message(lambda m: m.text == "⬅️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    from keyboards import main_kb
    await message.answer("Главное меню:", reply_markup=main_kb)
    # Обработчик для кнопки добавления расхода
@router.message(lambda m: m.text == "📤 Добавить расход")
async def handle_expense_button(message: Message, state: FSMContext):
    await add_expense_start(message, state)