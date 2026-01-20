# handlers/debts.py
import datetime
import logging
from aiogram import Router, F
from aiogram.types import Message, KeyboardButton  # Исправление: добавлен KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder # Для динамического списка долгов
from utils.user_manager import sheets_manager
from keyboards import main_kb, debt_kb

router = Router()
logger = logging.getLogger(__name__)

class DebtStates(StatesGroup):
    name = State()
    total_amount = State() # Используется ТОЛЬКО при создании нового долга
    percent = State()      # Используется ТОЛЬКО при создании нового долга
    payment_amount = State() # Выбор долга для оплаты
    pay_sum = State()        # Ввод суммы платежа (НОВОЕ)

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
            # ID(0), Название(1), Нач. сумма(2), Остаток(3), %(4)
            name = row[1]
            remaining = float(str(row[3]).replace(',', '.'))
            percent = row[4]
            total_remaining += remaining
            text += f"• {name}: {remaining:,.0f} ₽ ({percent}%)\n"
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
        raw_percent = message.text.replace('%', '').replace(',', '.')
        percent = float(raw_percent)
        
        values = [
            user_id, 
            str(data['name']), 
            float(data['total_amount']), 
            float(data['total_amount']), 
            percent, 
            datetime.date.today().strftime("%d.%m.%Y")
        ]
        
        sheets_manager.sheet_debts.append_row(values)
        await message.answer(f"✅ Долг «{data['name']}» добавлен!", reply_markup=debt_kb)
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите процент числом (например: 22)")
    except Exception as e:
        logger.error(f"Ошибка сохранения долга: {e}")
        await message.answer("❌ Ошибка при записи в таблицу.")

# --- ВНЕСЕНИЕ ПЛАТЕЖА (ИСПРАВЛЕННАЯ ЛОГИКА) ---
@router.message(F.text == "💸 Внести платеж")
async def pay_debt_start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    debts = sheets_manager.get_user_data(sheets_manager.sheet_debts, user_id)
    
    if not debts:
        await message.answer("⚠️ У вас нет активных долгов для оплаты.")
        return
    
    builder = ReplyKeyboardBuilder()
    for row in debts:
        builder.add(KeyboardButton(text=row[1]))
    
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2)
    
    await state.set_state(DebtStates.payment_amount) 
    await message.answer(
        "Выберите долг для погашения:", 
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

@router.message(DebtStates.payment_amount)
async def process_debt_choice(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Отменено", reply_markup=main_kb)
        return

    debt_name = message.text
    user_id = str(message.from_user.id)
    debts = sheets_manager.get_user_data(sheets_manager.sheet_debts, user_id)
    
    current_val = 0
    for row in debts:
        if row[1] == debt_name:
            current_val = float(str(row[3]).replace(',', '.'))
            break

    await state.update_data(selected_debt=debt_name, max_limit=current_val)
    
    # ВАЖНО: Переходим в состояние pay_sum, а не total_amount!
    await state.set_state(DebtStates.pay_sum) 
    
    await message.answer(
        f"💳 Вы выбрали «{debt_name}». Долг: {current_val:,.2f}\n"
        f"Введите сумму, которую вы внесли:",
        reply_markup=ReplyKeyboardBuilder().add(KeyboardButton(text="⬅️ Назад")).as_markup(resize_keyboard=True)
    )

# НОВЫЙ ОБРАБОТЧИК: Ловит ввод суммы и СРАЗУ сохраняет
@router.message(DebtStates.pay_sum)
async def process_payment_final(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Отменено", reply_markup=debt_kb)
        return

    try:
        payment = float(message.text.replace(' ', '').replace(',', '.'))
        data = await state.get_data()
        debt_name = data.get('selected_debt')
        max_limit = data.get('max_limit', 0)
        user_id = str(message.from_user.id)

        if payment > max_limit:
            await message.answer(f"⚠️ Сумма ({payment:,.2f}) больше долга ({max_limit:,.2f}).")
            return

        # 1. Записываем в лист расходов (Expense)
        today = datetime.date.today().strftime("%d.%m.%Y")
        exp_values = [user_id, today, "Личное", f"💳 Погашение: {debt_name}", payment]
        sheets_manager.append_user_row(sheets_manager.sheet_expense, user_id, exp_values)

        # 2. ОБНОВЛЕНИЕ ОСТАТКА В ТАБЛИЦЕ DEBTS
        new_rem = max(0, max_limit - payment)
        
        # Получаем все данные из листа долгов
        all_debts = sheets_manager.sheet_debts.get_all_values()
        
        # Ищем строку: ID пользователя в столбце A и Название в столбце B
        row_index = -1
        for i, row in enumerate(all_debts):
            if len(row) > 1 and row[0] == user_id and row[1] == debt_name:
                row_index = i + 1  # +1 так как в Google Sheets нумерация с 1
                break
        
        if row_index != -1:
            # Обновляем ячейку в столбце D (4-й столбец) — новый остаток
            sheets_manager.sheet_debts.update_cell(row_index, 4, new_rem)
            
            # Если долг погашен полностью (остаток 0), можно либо оставить 0, 
            # либо удалить строку. Давай пока просто оставим 0 для истории.
            status_msg = "Долг полностью погашен! 🎉" if new_rem == 0 else f"Остаток обновлен: {new_rem:,.2f} ₽"
        else:
            status_msg = "⚠️ Запись в таблице долгов не найдена, но расход записан."

        await message.answer(
            f"✅ Платеж {payment:,.2f} ₽ принят!\n"
            f"📉 {status_msg}",
            reply_markup=main_kb
        )
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите сумму числом.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении остатка: {e}")
        await message.answer("❌ Ошибка при связи с таблицей.")
