# handlers/income_work.py
import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.user_manager import sheets_manager
from keyboards import main_kb, get_income_kb, get_work_kb

router = Router()

class FinanceStates(StatesGroup):
    choosing_category = State()
    entering_amount = State()
    # Для работы
    work_request_num = State()
    work_repair_sum = State()
    work_my_share = State()
    work_tips = State()

# --- ЛИЧНЫЙ ДОХОД ---
@router.message(F.text == "💰 Доход")
async def income_start(message: Message, state: FSMContext):
    await state.set_state(FinanceStates.choosing_category)
    await message.answer("Откуда деньги?", reply_markup=get_income_kb())

@router.message(FinanceStates.choosing_category, F.text.in_(["💰 Зарплата", "🎁 Подарок", "📈 Кэшбэк", "📦 Продажа вещей", "🔄 Прочее"]))
async def process_income_cat(message: Message, state: FSMContext):
    await state.update_data(category=message.text, type="Личное")
    await state.set_state(FinanceStates.entering_amount)
    await message.answer(f"Сумма ({message.text}):")

@router.message(FinanceStates.entering_amount)
async def save_personal_income(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        user_id = str(message.from_user.id)
        today = datetime.date.today().strftime("%d.%m.%Y")
        
        # Запись: Дата | Тип | Категория | № Заявки | Чек | Доход | Долг | Статус
        values = [today, data['type'], data['category'], "-", amount, amount, 0, "Нет долга"]
        sheets_manager.append_user_row(sheets_manager.sheet_income, user_id, values)
        
        await message.answer(f"✅ Записал: +{amount}₽", reply_markup=main_kb)
        await state.clear()
    except:
        await message.answer("Введите число!")

# --- РАБОТА (ХОЛОДИЛЬЩИК) ---
@router.message(F.text == "❄️ Работа")
async def work_menu(message: Message):
    await message.answer("Раздел 'Работа'", reply_markup=get_work_kb())

@router.message(F.text.in_(["🏢 Фирма", "📱 Авито", "👥 Сарафанка"]))
async def start_work_entry(message: Message, state: FSMContext):
    await state.update_data(source=message.text)
    if message.text == "🏢 Фирма":
        await state.set_state(FinanceStates.work_request_num)
        await message.answer("Номер заявки:")
    else:
        await state.set_state(FinanceStates.work_repair_sum)
        await message.answer("Сумма по чеку:")

# ... (далее идет ваша старая логика из income.py, но с записью типа "Работа")
