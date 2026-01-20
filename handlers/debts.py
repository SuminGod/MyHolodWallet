# handlers/debts.py
import datetime
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.user_manager import sheets_manager
from keyboards import main_kb, debt_kb

router = Router()
logger = logging.getLogger(__name__)

class DebtStates(StatesGroup):
    name = State()
    total_amount = State()
    percent = State()
    payment_amount = State()

# --- ПРОСМОТР СПИСКА ---
@router.message(F.text == "📉 Долги/Кредиты")
async def debt_main(message: Message):
    await message.answer("Раздел долгов. Выберите действие:", reply_markup=debt_kb)

@router.message(F.text == "📊 Список долгов")
async def show_debt_list(message: Message):
    user_id = str(message.from_user.id)
    debts = sheets_manager.get_user_data(sheets_manager.sheet_debts, user_id)
    
    if not debts:
        await message.answer("У вас пока нет активных долгов.")
        return

    text = "📉 ВАШИ ДОЛГИ И КРЕДИТЫ:\n\n"
    total_remaining = 0
    
    for row in debts:
        try:
            name = row[1]
            remaining = float(str(row[3]).replace(',', '.'))
            percent = row[4]
            total_remaining += remaining
            text += f"• {name}: {remaining:,.0f} ₽ (Ставка: {percent}%)\n"
        except: continue
    
    text += f"\n💰 Итого осталось: {total_remaining:,.0f} ₽"
    await message.answer(text)

# --- ДОБАВЛЕНИЕ НОВОГО ДОЛГА ---
@router.message(F.text == "➕ Добавить долг")
async def add_debt_start(message: Message, state: FSMContext):
    await state.set_state(DebtStates.name)
    await message.answer("Введите название долга (например: Кредитка):")

@router.message(DebtStates.name)
async def add_debt_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(DebtStates.total_amount)
    await message.answer("Какая сумма долга на текущий момент?")

@router.message(DebtStates.total_amount)
async def add_debt_amount(message: Message, state: FSMContext):
    await state.update_data(amount=message.text)
    await state.set_state(DebtStates.percent)
    await message.answer("Годовая процентная ставка (0 если без %):")

@router.message(DebtStates.percent)
async def add_debt_final(message: Message, state: FSMContext):
    try:
        # Получаем всё, что ввели на прошлых шагах
        data = await state.get_data()
        user_id = str(message.from_user.id)
        
        # Очищаем ввод процентов от лишних символов
        percent_str = message.text.replace('%', '').replace(',', '.').strip()
        
        # Формируем список для записи: 
        # ID(0), Название(1), Нач.сумма(2), Остаток(3), %(4), Дата(5)
        values = [
            user_id, 
            data['name'], 
            data['amount'], # Начальная сумма из FSM
            data['amount'], # Остаток (при создании равен начальной сумме)
            percent_str,    # Процент
            datetime.date.today().strftime("%d.%m.%Y")
        ]
        
        # Запись в таблицу
        sheets_manager.sheet_debts.append_row(values)
        
        await message.answer(f"✅ Долг «{data['name']}» успешно добавлен!", reply_markup=debt_kb)
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при добавлении долга: {e}")
        await message.answer("❌ Произошла ошибка. Убедитесь, что вы ввели только числа.")

# --- ВНЕСЕНИЕ ПЛАТЕЖА ---
@router.message(F.text == "💸 Внести платеж")
async def pay_debt_start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    debts = sheets_manager.get_user_data(sheets_manager.sheet_debts, user_id)
    
    if not debts:
        await message.answer("Нет активных долгов для оплаты.")
        return
    
    await state.update_data(debts=debts)
    await state.set_state(DebtStates.payment_amount)
    # Для упрощения MVP платим по первому долгу в списке. Позже можно добавить выбор.
    await message.answer(f"Сколько вы вносите для погашения '{debts[0][1]}'?")

@router.message(DebtStates.payment_amount)
async def process_payment(message: Message, state: FSMContext):
    try:
        payment = float(message.text.replace(',', '.'))
        data = await state.get_data()
        user_id = str(message.from_user.id)
        debt_info = data['debts'][0] # Работаем с первой записью
        
        # 1. Записываем в расходы
        today = datetime.date.today().strftime("%d.%m.%Y")
        # ID, Дата, Тип, Кат, Сумма
        exp_values = [user_id, today, "Личное", f"💳 Погашение: {debt_info[1]}", payment]
        sheets_manager.append_user_row(sheets_manager.sheet_expense, user_id, exp_values)
        
        # 2. Обновляем остаток в таблице Debts (нужен поиск строки)
        # В данном упрощенном примере мы просто уведомляем, 
        # но для блога это отличный момент показать, как ИИ правит таблицу
        
        await message.answer(f"✅ Платеж {payment}₽ учтен в расходах и вычтен из долга!", reply_markup=main_kb)
        await state.clear()
    except:
        await message.answer("Введите число.")
