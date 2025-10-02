# handlers/income.py
import datetime
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import gspread
from gspread.exceptions import APIError
from utils.cancel_handler import cancel_handler

from keyboards import main_kb, income_kb, tips_kb
from config import GSHEET_NAME, GSHEET_CREDS_JSON

router = Router()

# Подключение к Google Sheets
from config import GSHEET_CREDS
import gspread

if GSHEET_CREDS:
    gc = gspread.service_account_from_dict(GSHEET_CREDS)
else:
    gc = gspread.service_account(filename='creds.json')

sheet_income = gc.open(GSHEET_NAME).worksheet("Доходы")
sheet_tips = gc.open(GSHEET_NAME).worksheet("Чаевые")

class IncomeStates(StatesGroup):
    source = State()
    request_number = State()
    amount = State()
    my_income = State()
    tips = State()

class TipsStates(StatesGroup):
    type = State()
    amount = State()
    comment = State()

# ========== ДОХОДЫ ==========
@router.message(lambda m: m.text == "💵 Добавить доход")
async def add_income_start(message: Message, state: FSMContext):
    await state.set_state(IncomeStates.source)
    await message.answer("Откуда заявка?", reply_markup=income_kb)

@router.message(IncomeStates.source)
async def process_income_source(message: Message, state: FSMContext):
    if await cancel_handler(message, state):
        return
    
    await state.update_data(source=message.text)
    
    if message.text == "🏢 Фирма":
        await state.set_state(IncomeStates.request_number)
        await message.answer("🔢 Номер заявки от фирмы:")
    else:  # Авито/Сарафанка
        await state.set_state(IncomeStates.amount) 
        await message.answer("💰 Сколько получил по чеку?")

@router.message(IncomeStates.request_number)
async def process_request_number(message: Message, state: FSMContext):
    await state.update_data(request_number=message.text)
    await state.set_state(IncomeStates.amount)
    await message.answer("💰 Общая сумма по чеку фирмы:")

@router.message(IncomeStates.amount)
async def process_income_amount(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        source = data["source"]
        amount = float(message.text.replace(',', '.'))
        
        if source == "🏢 Фирма":
            await state.update_data(repair_amount=amount)
            await state.set_state(IncomeStates.my_income)
            await message.answer("💸 Сколько твой доход по чеку?")
        else:
            # Авито/Сарафанка - вся сумма это мой доход
            await state.update_data(my_income=amount)
            await state.set_state(IncomeStates.tips)
            await message.answer("💝 Были чаевые? (Если нет - напиши 0)")
            
    except ValueError:
        await message.answer("❌ Введи нормальную сумму:")

@router.message(IncomeStates.my_income)
async def process_my_income(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        my_income = float(message.text.replace(',', '.'))
        repair_amount = data["repair_amount"]
        
        if my_income > repair_amount:
            await message.answer("❌ Твой доход не может быть больше общей суммы. Введи корректную сумму:")
            return
            
        await state.update_data(my_income=my_income)
        await state.set_state(IncomeStates.tips)
        await message.answer("💝 Были чаевые? (Если нет - напиши 0)")
        
    except ValueError:
        await message.answer("❌ Введи нормальную сумму:")

@router.message(IncomeStates.tips)
async def process_tips(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        source = data["source"]
        request_number = data.get('request_number', '')
        repair_amount = data.get("repair_amount", 0)
        my_income = data["my_income"]
        tips = float(message.text.replace(',', '.')) if message.text != "0" else 0
        
        # Расчет долга фирме (только для фирмы)
        debt_to_firm = repair_amount - my_income if source == "🏢 Фирма" else 0
        
        today = datetime.date.today().strftime("%d.%m.%Y")
        
        # Записываем основной доход (БЕЗ чаевых в этой таблице)
        values = [today, source, request_number, repair_amount, my_income, debt_to_firm]
        sheet_income.append_row(values)
        
        # Если есть чаевые - записываем их ОТДЕЛЬНО
        if tips > 0:
            tip_type = "Чаевые с заявки"
            tip_comment = f"Заявка {request_number} ({source})" if request_number else f"{source}"
            tip_values = [today, tip_type, tips, tip_comment]
            sheet_tips.append_row(tip_values)
        
        # Формируем ответ
        response = f"✅ Доход добавлен:\n"
        if source == "🏢 Фирма":
            response += f"🔢 Заявка: {request_number}\n"
            response += f"💵 Сумма чека: {repair_amount} ₽\n"
            response += f"💸 Твой доход: {my_income} ₽\n"
            response += f"🏢 Долг фирме: {debt_to_firm} ₽\n"
        else:
            response += f"💸 Твой доход: {my_income} ₽\n"
            
        if tips > 0:
            response += f"💝 Чаевые: +{tips} ₽\n"
            response += f"🎯 Итого: {my_income + tips} ₽"
        
        await message.answer(response, reply_markup=main_kb)
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введи нормальную сумму для чаевых (или 0 если нет):")

# ========== ЧАЕВЫЕ ==========
@router.message(lambda m: m.text == "💰 Чаевые")
async def add_tips_start(message: Message, state: FSMContext):
    await state.set_state(TipsStates.type)
    await message.answer("Что за дополнительный доход?", reply_markup=tips_kb)

@router.message(TipsStates.type)
async def process_tips_type(message: Message, state: FSMContext):
    if await cancel_handler(message, state):
        return
        
    await state.update_data(tip_type=message.text)
    await state.set_state(TipsStates.amount)
    await message.answer("💰 Сколько получил?")

@router.message(TipsStates.amount)
async def process_tips_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        await state.update_data(amount=amount)
        await state.set_state(TipsStates.comment)
        await message.answer("📝 Комментарий (от кого/за что):")
        
    except ValueError:
        await message.answer("❌ Введи нормальную сумму:")

@router.message(TipsStates.comment)
async def process_tips_comment(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        tip_type = data["tip_type"]
        amount = data["amount"]
        comment = message.text
        
        today = datetime.date.today().strftime("%d.%m.%Y")
        values = [today, tip_type, amount, comment]
        sheet_tips.append_row(values)
        
        await message.answer(f"✅ Чаевые добавлены: {amount} ₽\n{tip_type}: {comment}", reply_markup=main_kb)
        await state.clear()
        
    except Exception as e:
        await message.answer("❌ Ошибка при добавлении чаевых")
        # ОБРАБОТКА ЛЮБЫХ НЕОБРАБОТАННЫХ СООБЩЕНИЙ
        
    # Обработка кнопки "Назад" из любого состояния
@router.message(lambda m: m.text == "⬅️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    from keyboards import main_kb
    await message.answer("Главное меню:", reply_markup=main_kb)
    
    # Обработчики для кнопок главного меню в роутере доходов
@router.message(lambda m: m.text == "💵 Добавить доход")
async def handle_income_button(message: Message, state: FSMContext):
    await add_income_start(message, state)

@router.message(lambda m: m.text == "💰 Чаевые")
async def handle_tips_button(message: Message, state: FSMContext):

    await add_tips_start(message, state)
