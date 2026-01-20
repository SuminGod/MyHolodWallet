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
            text += f"• {name}: {remaining:,.0f} ₽ ({percent}%)\n"
        except: continue
    
    text += f"\n💰 Итого осталось: {total_remaining:,.0f} ₽"
    await message.answer(text)

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
    # Очищаем ввод от пробелов и запятых
    raw_amount = message.text.replace(' ', '').replace(',', '.')
    try:
        amount = float(raw_amount)
        await state.update_data(total_amount=amount)
        await state.set_state(DebtStates.percent)
        await message.answer("Годовая процентная ставка (0 если без %):")
    except ValueError:
        await message.answer("❌ Введите сумму числом (например: 840000)")

@router.message(DebtStates.percent)
async def add_debt_final(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = str(message.from_user.id)
        
        # Очищаем ввод процентов
        raw_percent = message.text.replace('%', '').replace(',', '.')
        percent = float(raw_percent)
        
        # Формируем список для записи в Google Sheets:
        # A: ID, B: Название, C: Нач. сумма, D: Остаток, E: %, F: Дата
        values = [
            user_id, 
            str(data['name']), 
            float(data['total_amount']), 
            float(data['total_amount']), 
            percent, 
            datetime.date.today().strftime("%d.%m.%Y")
        ]
        
        # Запись в таблицу
        sheets_manager.sheet_debts.append_row(values)
        
        await message.answer(f"✅ Долг «{data['name']}» добавлен!", reply_markup=debt_kb)
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите процент числом (например: 22)")
    except Exception as e:
        logger.error(f"Ошибка сохранения долга: {e}")
        await message.answer(f"❌ Ошибка при записи в таблицу.")

# --- ВНЕСЕНИЕ ПЛАТЕЖА ---
@router.message(F.text == "💸 Внести платеж")
async def pay_debt_start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    # Получаем данные пользователя из листа Debts
    debts = sheets_manager.get_user_data(sheets_manager.sheet_debts, user_id)
    
    if not debts:
        await message.answer("⚠️ У вас нет активных долгов для оплаты.")
        return
    
    # Сохраняем долги в состояние, чтобы не скачивать их снова
    await state.update_data(user_debts=debts)
    await state.set_state(DebtStates.payment_amount)
    
    # Показываем название первого долга для оплаты (индекс 1, так как 0 - это ID)
    debt_name = debts[0][1] 
    await message.answer(f"💰 Введите сумму платежа для погашения «{debt_name}»:")

@router.message(DebtStates.payment_amount)
async def process_payment(message: Message, state: FSMContext):
    try:
        # Очищаем ввод
        payment_raw = message.text.replace(' ', '').replace(',', '.')
        payment = float(payment_raw)
        
        data = await state.get_data()
        user_id = str(message.from_user.id)
        
        # Берем информацию о первом долге из сохраненных данных
        # Структура: ID(0), Название(1), Нач.сумма(2), Остаток(3), %(4)
        debt_info = data['user_debts'][0]
        debt_name = debt_info[1]
        current_remaining = float(str(debt_info[3]).replace(',', '.'))
        
        # 1. Записываем платеж в лист РАСХОДОВ (Expense)
        today = datetime.date.today().strftime("%d.%m.%Y")
        # ID(0), Дата(1), Тип(2), Кат(3), Сумма(4)
        exp_values = [user_id, today, "Личное", f"💳 Погашение: {debt_name}", payment]
        sheets_manager.append_user_row(sheets_manager.sheet_expense, user_id, exp_values)
        
        # 2. Высчитываем новый остаток
        new_remaining = max(0, current_remaining - payment)
        
        await message.answer(
            f"✅ Платеж {payment:,.0f} ₽ учтен!\n"
            f"📉 Остаток по долгу «{debt_name}»: {new_remaining:,.0f} ₽\n\n"
            f"Данные обновлены в таблице расходов.", 
            reply_markup=main_kb
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите сумму платежа цифрами.")
    except Exception as e:
        logger.error(f"Ошибка при внесении платежа: {e}")
        await message.answer("❌ Произошла ошибка при обработке платежа.")
