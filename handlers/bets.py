# handlers/bets.py
import datetime
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import gspread
from gspread.exceptions import APIError

from keyboards import main_kb, bets_kb, bets_report_kb
from config import GSHEET_NAME, GSHEET_CREDS_JSON

router = Router()
logger = logging.getLogger(__name__)

# Подключение к Google Sheets
try:
    gc = gspread.service_account(filename=GSHEET_CREDS_JSON)
    sheet_bets = gc.open(GSHEET_NAME).worksheet("Ставки")
    logger.info("✅ Таблица 'Ставки' подключена")
except Exception as e:
    logger.error(f"❌ Ошибка подключения к таблице 'Ставки': {e}")
    # Создаем заглушку чтобы бот не падал
    sheet_bets = None

class BetsStates(StatesGroup):
    operation_type = State()
    amount = State()

class BetsReportStates(StatesGroup):
    period = State()

# ========== СТАВКИ - ГЛАВНОЕ МЕНЮ ==========
@router.message(lambda m: m.text == "🎯 Ставки")
async def bets_main(message: Message):
    await message.answer("💰 Учет ставок:", reply_markup=bets_kb)

# ========== ПОПОЛНЕНИЕ/ВЫВОД ==========
@router.message(lambda m: m.text in ["💰 Пополнение", "💸 Вывод"])
async def start_bet_operation(message: Message, state: FSMContext):
    operation_type = "Пополнение" if message.text == "💰 Пополнение" else "Вывод"
    await state.update_data(operation_type=operation_type)
    await state.set_state(BetsStates.amount)
    
    if operation_type == "Пополнение":
        await message.answer("💰 Сколько пополнил?")
    else:
        await message.answer("💸 Сколько вывел?")

@router.message(BetsStates.amount)
async def process_bet_amount(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        operation_type = data["operation_type"]
        amount = float(message.text.replace(',', '.'))
        
        today = datetime.date.today().strftime("%d.%m.%Y")
        
        # Записываем в таблицу
        if sheet_bets:
            values = [today, operation_type, amount]
            sheet_bets.append_row(values)
        
        if operation_type == "Пополнение":
            response = f"✅ Пополнение добавлено: +{amount} ₽"
        else:
            response = f"✅ Вывод добавлен: -{amount} ₽"
        
        await message.answer(response, reply_markup=bets_kb)
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введи нормальную сумму:")
    except APIError as e:
        await message.answer("❌ Ошибка записи в таблицу")
        logger.error(f"Bets API error: {e}")

# ========== ОТЧЕТЫ ПО СТАВКАМ ==========
@router.message(lambda m: m.text == "📊 Отчет ставок")
async def start_bets_report(message: Message, state: FSMContext):
    await state.set_state(BetsReportStates.period)
    await message.answer("За какой период отчет по ставкам?", reply_markup=bets_report_kb)

@router.message(BetsReportStates.period)
async def generate_bets_report(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_kb)
        return
        
    try:
        if not sheet_bets:
            await message.answer("❌ Таблица ставок не доступна")
            return
            
        bets_data = sheet_bets.get_all_values()[1:]  # пропускаем заголовок
        
        today = datetime.date.today()
        
        if message.text == "🎯 День ставок":
            start_date = today
            period_text = "за день"
        elif message.text == "🎯 Неделя ставок":
            start_date = today - datetime.timedelta(days=7)
            period_text = "за неделю"
        elif message.text == "🎯 Месяц ставок":
            start_date = today - datetime.timedelta(days=30)
            period_text = "за месяц"
        else:  # Год ставок
            start_date = today - datetime.timedelta(days=365)
            period_text = "за год"
        
        # Расчеты
        total_deposits = 0
        total_withdrawals = 0
        deposits_count = 0
        withdrawals_count = 0
        
        for row in bets_data:
            if len(row) >= 3:
                try:
                    row_date = datetime.datetime.strptime(row[0], "%d.%m.%Y").date()
                    if row_date >= start_date:
                        operation_type = row[1]
                        amount = float(row[2]) if row[2] else 0
                        
                        if operation_type == "Пополнение":
                            total_deposits += amount
                            deposits_count += 1
                        elif operation_type == "Вывод":
                            total_withdrawals += amount
                            withdrawals_count += 1
                except:
                    continue
        
        # Расчет разницы
        difference = total_withdrawals - total_deposits
        difference_sign = "➕" if difference > 0 else "➖"
        
        response = (
            f"🎯 ОТЧЕТ ПО СТАВКАМ {period_text.upper()}:\n"
            f"💰 Пополнений: {deposits_count} шт\n"
            f"💵 Сумма пополнений: {total_deposits:,.0f} ₽\n"
            f"💸 Выводов: {withdrawals_count} шт\n"
            f"💳 Сумма выводов: {total_withdrawals:,.0f} ₽\n"
            f"📊 Разница: {difference_sign}{abs(difference):,.0f} ₽\n\n"
        )
        
        # Добавляем анализ
        if difference > 0:
            response += f"✅ В плюсе на {difference:,.0f} ₽"
        elif difference < 0:
            response += f"❌ В минусе на {abs(difference):,.0f} ₽"
        else:
            response += f"⚖️ В ноль"
        
        await message.answer(response, reply_markup=bets_kb)
        await state.clear()
        
    except Exception as e:
        await message.answer("❌ Ошибка формирования отчета по ставкам")
        logger.error(f"Bets report error: {e}")

# Обработка кнопки "Назад" в меню ставок
@router.message(lambda m: m.text == "⬅️ Назад")
async def back_from_bets(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_kb)
    # Обработка кнопки "Назад" из любого состояния
@router.message(lambda m: m.text == "⬅️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    from keyboards import main_kb
    await message.answer("Главное меню:", reply_markup=main_kb)
    
    # Обработчик для кнопки ставок
@router.message(lambda m: m.text == "🎯 Ставки")
async def handle_bets_button(message: Message):
    await bets_main(message)