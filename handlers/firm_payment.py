# handlers/firm_payment.py
import datetime
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton
import gspread

from keyboards import main_kb
from utils.user_manager import sheets_manager

router = Router()

class PaymentStates(StatesGroup):
    confirm = State()

def confirm_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Подтвердить оплату "))
    builder.add(KeyboardButton(text="❌ Отмена"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

@router.message(lambda m: m.text == "💳 Отметить оплату фирме")
async def start_payment_process(message: Message, state: FSMContext):
    """Начало процесса отметки оплаты"""
    
    user_id = str(message.from_user.id)
    
    # Получаем все неоплаченные заявки фирмы для этого пользователя
    incomes = sheets_manager.get_user_data(sheets_manager.sheet_income, user_id)
    
    unpaid_requests = []
    total_debt = 0
    
    # Ищем строки для обновления
    all_incomes = sheets_manager.get_all_data(sheets_manager.sheet_income)
    
    for i, row in enumerate(all_incomes, start=1):
        if len(row) >= 8 and row[0] == user_id and row[2] == "🏢 Фирма" and row[7] == "Не оплачено":
            try:
                debt = float(row[6]) if row[6] else 0
                if debt > 0:
                    unpaid_requests.append({
                        'row_index': i,
                        'date': row[1],
                        'request_number': row[3],
                        'debt': debt
                    })
                    total_debt += debt
            except:
                continue
    
    if not unpaid_requests:
        await message.answer("✅ Нет неоплаченных заявок!", reply_markup=main_kb)
        return
    
    await state.update_data(unpaid_requests=unpaid_requests, total_debt=total_debt)
    
    # Формируем список заявок для подтверждения
    requests_text = "\n".join([f"{req['date']} - {req['request_number']} - {req['debt']:,.0f} ₽" 
                              for req in unpaid_requests[:10]])  # показываем первые 10
    
    if len(unpaid_requests) > 10:
        requests_text += f"\n... и еще {len(unpaid_requests) - 10} заявок"
    
    response = (
        f"💳 ОПЛАТА ФИРМЕ\n"
        f"📋 Неоплаченных заявок: {len(unpaid_requests)}\n"
        f"💰 Общий долг: {total_debt:,.0f} ₽\n\n"
        f"📋 Заявки:\n{requests_text}\n\n"
        f"✅ Подтвердить оплату всей суммы?"
    )
    
    await message.answer(response, reply_markup=confirm_kb())
    await state.set_state(PaymentStates.confirm)

@router.message(PaymentStates.confirm)
async def confirm_payment(message: Message, state: FSMContext):
    if message.text == "❌ Отмена" or message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Отмена оплаты", reply_markup=main_kb)
        return
        
    if message.text == "✅ Подтвердить оплату":
        data = await state.get_data()
        unpaid_requests = data['unpaid_requests']
        total_debt = data['total_debt']
        
        # Обновляем статус всех неоплаченных заявок
        updated_count = 0
        for request in unpaid_requests:
            try:
                sheets_manager.sheet_income.update_cell(request['row_index'], 8, "Оплачено")  # 8-й столбец - статус
                updated_count += 1
            except Exception as e:
                print(f"Error updating row {request['row_index']}: {e}")
        
        await message.answer(
            f"✅ Оплата подтверждена!\n"
            f"📋 Заявок оплачено: {updated_count}\n"
            f"💰 Сумма: {total_debt:,.0f} ₽\n"
            f"🏢 Долг перед фирмой обнулен!",
            reply_markup=main_kb
        )
        await state.clear()
    else:
        await message.answer("Используй кнопки для подтверждения")

# Обработка кнопки "Назад"
@router.message(lambda m: m.text == "⬅️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_kb)
