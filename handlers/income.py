# handlers/income.py
import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.cancel_handler import cancel_handler
from utils.user_manager import sheets_manager
from keyboards import main_kb, get_income_kb, get_work_kb

router = Router()

class IncomeStates(StatesGroup):
    category = State()
    amount = State()
    # Состояния для работы
    work_source = State()
    request_number = State()
    repair_amount = State()
    my_income = State()
    tips = State()

# ========== ЛИЧНЫЕ ДОХОДЫ (ГЛАВНОЕ МЕНЮ) ==========
@router.message(F.text == "💰 Доход")
async def add_income_start(message: Message, state: FSMContext):
    await state.set_state(IncomeStates.category)
    await message.answer("Выберите категорию дохода:", reply_markup=get_income_kb())

@router.message(IncomeStates.category)
async def process_income_category(message: Message, state: FSMContext):
    if await cancel_handler(message, state): return
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_kb)
        return
    
    await state.update_data(category=message.text)
    await state.set_state(IncomeStates.amount)
    await message.answer(f"Введите сумму ({message.text}):")

@router.message(IncomeStates.amount)
async def process_income_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        user_id = str(message.from_user.id)
        today = datetime.date.today().strftime("%d.%m.%Y")
        
        # Записываем в таблицу Income: Дата | Тип | Категория | № Заявки | Чек | Доход | Долг | Статус
        values = [today, "Личное", data['category'], "-", amount, amount, 0, "Нет долга"]
        sheets_manager.append_user_row(sheets_manager.sheet_income, user_id, values)
        
        await message.answer(f"✅ Доход {amount}₽ записан!", reply_markup=main_kb)
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

# ========== РАБОТА (ХОЛОДИЛЬЩИК) ==========
@router.message(F.text == "❄️ Работа")
async def work_menu(message: Message):
    await message.answer("Раздел работы. Выберите источник:", reply_markup=get_work_kb())

@router.message(F.text.in_(["🏢 Фирма", "📱 Авито", "👥 Сарафанка"]))
async def start_work_job(message: Message, state: FSMContext):
    source = message.text
    await state.update_data(source=source)
    
    if source == "🏢 Фирма":
        await state.set_state(IncomeStates.request_number)
        await message.answer("🔢 Номер заявки от фирмы:")
    else:
        await state.set_state(IncomeStates.repair_amount)
        await message.answer("💰 Сколько получил по чеку?")

@router.message(IncomeStates.request_number)
async def process_req_num(message: Message, state: FSMContext):
    await state.update_data(request_number=message.text)
    await state.set_state(IncomeStates.repair_amount)
    await message.answer("💰 Общая сумма по чеку фирмы:")

@router.message(IncomeStates.repair_amount)
async def process_repair_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        await state.update_data(repair_amount=amount)
        
        if data['source'] == "🏢 Фирма":
            await state.set_state(IncomeStates.my_income)
            await message.answer("💸 Твой доход из этой суммы?")
        else:
            await state.update_data(my_income=amount)
            await state.set_state(IncomeStates.tips)
            await message.answer("💝 Были чаевые? (0 если нет)")
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(IncomeStates.my_income)
async def process_my_income(message: Message, state: FSMContext):
    try:
        my_income = float(message.text.replace(',', '.'))
        await state.update_data(my_income=my_income)
        await state.set_state(IncomeStates.tips)
        await message.answer("💝 Были чаевые? (0 если нет)")
    except ValueError:
        await message.answer("❌ Введите число!")

@router.message(IncomeStates.tips)
async def process_work_final(message: Message, state: FSMContext):
    try:
        tips = float(message.text.replace(',', '.'))
        data = await state.get_data()
        user_id = str(message.from_user.id)
        today = datetime.date.today().strftime("%d.%m.%Y")
        
        debt = data['repair_amount'] - data['my_income'] if data['source'] == "🏢 Фирма" else 0
        status = "Не оплачено" if debt > 0 else "Нет долга"
        
        # Запись: Дата | Тип | Источник | № Заявки | Чек | Доход | Долг | Статус
        values = [today, "Работа", data['source'], data.get('request_number', '-'), data['repair_amount'], data['my_income'], debt, status]
        sheets_manager.append_user_row(sheets_manager.sheet_income, user_id, values)
        
        if tips > 0:
            tip_values = [today, "Чаевые с заявки", tips, f"Заявка {data.get('request_number', data['source'])}"]
            sheets_manager.append_user_row(sheets_manager.sheet_tips, user_id, tip_values)

        await message.answer(f"✅ Работа записана!\nДоход: {data['my_income']}₽\nДолг: {debt}₽", reply_markup=get_work_kb())
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")
