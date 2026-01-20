# handlers/debts.py
import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards import get_debt_kb, main_kb

router = Router()

class DebtStates(StatesGroup):
    new_debt_name = State()
    new_debt_amount = State()
    new_debt_percent = State()

@router.message(F.text == "📉 Долги/Кредиты")
async def debt_main(message: Message):
    await message.answer("Управление долгами", reply_markup=get_debt_kb())

@router.message(F.text == "➕ Добавить долг")
async def add_debt_start(message: Message, state: FSMContext):
    await state.set_state(DebtStates.new_debt_name)
    await message.answer("Введите название (например: Кредитка Сбер):")

@router.message(DebtStates.new_debt_name)
async def add_debt_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(DebtStates.new_debt_amount)
    await message.answer("Какая сумма долга сейчас?")

@router.message(DebtStates.new_debt_amount)
async def add_debt_amount(message: Message, state: FSMContext):
    await state.update_data(amount=message.text)
    await state.set_state(DebtStates.new_debt_percent)
    await message.answer("Какая годовая ставка %? (0 если без %)")

@router.message(DebtStates.new_debt_percent)
async def add_debt_final(message: Message, state: FSMContext):
    data = await state.get_data()
    # Здесь будет логика записи в лист Debts таблицы
    await message.answer(f"✅ Долг '{data['name']}' на сумму {data['amount']}₽ добавлен!", reply_markup=get_debt_kb())
    await state.clear()
