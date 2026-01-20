import datetime
import logging
from aiogram import Router, F
from aiogram.types import Message, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from utils.user_manager import sheets_manager
from keyboards import main_kb, debt_kb

router = Router()
logger = logging.getLogger(__name__)

class DebtStates(StatesGroup):
    name = State()
    total_amount = State()
    percent = State()
    payment_amount = State()
    pay_sum = State()

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

    text = "📉 ВАШИ АКТИВНЫЕ ДОЛГИ:\n\n"
    total_remaining = 0
    active_count = 0
    
    for row in debts:
        try:
            remaining = float(str(row[3]).replace(',', '.'))
            if remaining <= 0: continue
            
            name = row[1]
            percent = row[4]
            total_remaining += remaining
            active_count += 1
            text += f"• {name}: {remaining:,.0f} ₽ ({percent}%)\n"
        except: continue
    
    if active_count == 0:
        await message.answer("🎉 Поздравляю! Все ваши долги погашены.")
        return

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
    try:
        amount = float(message.text.replace(' ', '').replace(',', '.'))
        await state.update_data(total_amount=amount)
        await state.set_state(DebtStates.percent)
        await message.answer("Годовая процентная ставка (0 если без %):")
    except:
        await message.answer("❌ Введите сумму числом.")

@router.message(DebtStates.percent)
async def add_debt_final(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = str(message.from_user.id)
        percent = float(message.text.replace('%', '').replace(',', '.'))
        
        values = [user_id, data['name'], data['total_amount'], data['total_amount'], percent, datetime.date.today().strftime("%d.%m.%Y")]
        sheets_manager.sheet_debts.append_row(values)
        
        await message.answer(f"✅ Долг «{data['name']}» добавлен!", reply_markup=debt_kb)
        await state.clear()
    except:
        await message.answer("❌ Ошибка. Введите процент числом.")

@router.message(F.text == "💸 Внести платеж")
async def pay_debt_start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    debts = sheets_manager.get_user_data(sheets_manager.sheet_debts, user_id)
    
    builder = ReplyKeyboardBuilder()
    has_active = False
    for row in debts:
        try:
            if float(str(row[3]).replace(',', '.')) > 0:
                builder.add(KeyboardButton(text=row[1]))
                has_active = True
        except: continue
    
    if not has_active:
        await message.answer("⚠️ Нет активных долгов.")
        return
    
    builder.add(KeyboardButton(text="⬅️ Назад")); builder.adjust(2)
    await state.set_state(DebtStates.payment_amount)
    await message.answer("Выберите долг для погашения:", reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(DebtStates.payment_amount)
async def process_debt_choice(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear(); await message.answer("Отменено", reply_markup=main_kb); return

    user_id = str(message.from_user.id)
    debts = sheets_manager.get_user_data(sheets_manager.sheet_debts, user_id)
    current_val = next((float(str(r[3]).replace(',', '.')) for r in debts if r[1] == message.text), 0)

    await state.update_data(selected_debt=message.text, max_limit=current_val)
    await state.set_state(DebtStates.pay_sum)
    await message.answer(f"💳 Вы выбрали «{message.text}». Долг: {current_val:,.2f}\nВведите сумму платежа:")

@router.message(DebtStates.pay_sum)
async def process_payment_final(message: Message, state: FSMContext):
    try:
        payment = float(message.text.replace(' ', '').replace(',', '.'))
        data = await state.get_data()
        if payment > data['max_limit']:
            await message.answer(f"⚠️ Сумма больше долга ({data['max_limit']})"); return

        user_id = str(message.from_user.id)
        # ЗАПИСЬ РАСХОДА (Исправлено смещение)
        exp_vals = [user_id, datetime.date.today().strftime("%d.%m.%Y"), "Личное", f"💳 Погашение: {data['selected_debt']}", payment]
        sheets_manager.sheet_expense.append_row(exp_vals)

        # ОБНОВЛЕНИЕ ОСТАТКА
        new_rem = max(0, data['max_limit'] - payment)
        all_rows = sheets_manager.sheet_debts.get_all_values()
        for i, row in enumerate(all_rows):
            if len(row) > 1 and row[0] == user_id and row[1] == data['selected_debt']:
                sheets_manager.sheet_debts.update_cell(i + 1, 4, str(new_rem).replace('.', ','))
                break

        await message.answer(f"✅ Принято! Новый остаток: {new_rem:,.2f} ₽", reply_markup=main_kb)
        await state.clear()
    except:
        await message.answer("❌ Введите число.")
