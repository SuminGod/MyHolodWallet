# handlers/reports.py
import datetime
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton
from utils.cancel_handler import cancel_handler
from utils.user_manager import sheets_manager

from keyboards import main_kb, report_kb, firm_report_kb

router = Router()
logger = logging.getLogger(__name__)

class FirmReportStates(StatesGroup):
    period = State()

class MonthReportStates(StatesGroup):
    select_month = State()

# ========== КЛАВИАТУРА ВЫБОРА МЕСЯЦА ==========
def get_months_kb():
    """Клавиатура для выбора месяца"""
    builder = ReplyKeyboardBuilder()
    
    # Текущий год и предыдущий
    current_year = datetime.datetime.now().year
    months_ru = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    
    # Добавляем месяцы текущего года
    current_month = datetime.datetime.now().month
    for i in range(current_month):
        builder.add(KeyboardButton(text=f"{months_ru[i]} {current_year}"))
    
    # Добавляем месяцы предыдущего года
    for i in range(12):
        builder.add(KeyboardButton(text=f"{months_ru[i]} {current_year-1}"))
    
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(3, 3, 3, 3, 3, 3, 1)
    return builder.as_markup(resize_keyboard=True)

# ========== ОТЧЕТЫ ==========
@router.message(lambda m: m.text == "📊 Отчет")
async def show_reports(message: Message):
    await message.answer("Какой отчет нужен?", reply_markup=report_kb)

@router.message(lambda m: m.text in ["📅 Сегодня", "📆 Неделя", "🗓️ Месяц", "📈 Год"])
async def generate_personal_report(message: Message, state: FSMContext):
    if message.text == "🗓️ Месяц":
        # Переходим к выбору конкретного месяца
        await state.set_state(MonthReportStates.select_month)
        await message.answer("Выбери месяц для отчета:", reply_markup=get_months_kb())
        return
        
    # Остальные отчеты (сегодня, неделя, год) работают как раньше
    await generate_period_report(message, message.text)

@router.message(MonthReportStates.select_month)
async def process_month_selection(message: Message, state: FSMContext):
    if await cancel_handler(message, state):
        return
        
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Главное меню:", reply_markup=main_kb)
        return
    
    # Парсим выбранный месяц
    try:
        month_text = message.text
        await generate_monthly_report(message, month_text)
        await state.clear()
    except Exception as e:
        await message.answer("❌ Ошибка при формировании отчета за месяц")
        logger.error(f"Month report error: {e}")

async def generate_monthly_report(message: Message, month_text: str):
    """Генерация отчета за конкретный месяц"""
    try:
        # Парсим месяц и год из текста
        months_ru = {
            "Январь": 1, "Февраль": 2, "Март": 3, "Апрель": 4, "Май": 5, "Июнь": 6,
            "Июль": 7, "Август": 8, "Сентябрь": 9, "Октябрь": 10, "Ноябрь": 11, "Декабрь": 12
        }
        
        parts = month_text.split()
        month_name = parts[0]
        year = int(parts[1])
        month = months_ru[month_name]
        
        # Определяем диапазон дат
        start_date = datetime.date(year, month, 1)
        if month == 12:
            end_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_date = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        
        await generate_report_by_dates(message, start_date, end_date, f"за {month_text.lower()}")
        
    except Exception as e:
        await message.answer("❌ Не могу распознать месяц. Выбери из списка.")
        logger.error(f"Month parsing error: {e}")

async def generate_period_report(message: Message, period_type: str):
    """Генерация отчета за стандартные периоды"""
    today = datetime.date.today()
    
    if period_type == "📅 Сегодня":
        start_date = today
        end_date = today
        period_text = "сегодня"
    elif period_type == "📆 Неделя":
        start_date = today - datetime.timedelta(days=7)
        end_date = today
        period_text = "за неделю"
    elif period_type == "📈 Год":
        start_date = today - datetime.timedelta(days=365)
        end_date = today
        period_text = "за год"
    else:  # Месяц (динамический)
        start_date = today - datetime.timedelta(days=30)
        end_date = today
        period_text = "за месяц"
    
    await generate_report_by_dates(message, start_date, end_date, period_text)

async def generate_report_by_dates(message: Message, start_date: datetime.date, end_date: datetime.date, period_text: str):
    """Общая функция генерации отчета по датам"""
    try:
        user_id = str(message.from_user.id)
        
        # Получаем данные только для этого пользователя
        incomes = sheets_manager.get_user_data(sheets_manager.sheet_income, user_id)
        expenses = sheets_manager.get_user_data(sheets_manager.sheet_expense, user_id)
        tips_data = sheets_manager.get_user_data(sheets_manager.sheet_tips, user_id)
        bets_data = sheets_manager.get_user_data(sheets_manager.sheet_bets, user_id)
        
        # Расчеты
        total_my_income = 0
        total_tips = 0
        total_expenses = 0
        total_bets_net = 0
        firm_count = 0
        avito_count = 0
        sarafanka_count = 0
        
        # Основные доходы (пропускаем первый элемент - user_id)
        for row in incomes:
            if len(row) >= 7:  # user_id + 6 полей
                try:
                    row_date = datetime.datetime.strptime(row[1], "%d.%m.%Y").date()  # row[1] - дата
                    if start_date <= row_date <= end_date:
                        my_income = float(row[5]) if row[5] else 0  # row[5] - мой доход
                        total_my_income += my_income
                        
                        source = row[2]  # row[2] - источник
                        if source == "🏢 Фирма":
                            firm_count += 1
                        elif source == "📱 Авито":
                            avito_count += 1
                        elif source == "👥 Сарафанка":
                            sarafanka_count += 1
                except:
                    continue
        
        # Чаевые
        for row in tips_data:
            if len(row) >= 4:  # user_id + 3 поля
                try:
                    row_date = datetime.datetime.strptime(row[1], "%d.%m.%Y").date()  # row[1] - дата
                    if start_date <= row_date <= end_date:
                        total_tips += float(row[3]) if row[3] else 0  # row[3] - сумма
                except:
                    continue
        
        # Расходы
        for row in expenses:
            if len(row) >= 4:  # user_id + 3 поля
                try:
                    row_date = datetime.datetime.strptime(row[1], "%d.%m.%Y").date()  # row[1] - дата
                    if start_date <= row_date <= end_date:
                        total_expenses += float(row[3]) if row[3] else 0  # row[3] - сумма
                except:
                    continue
        
        # Ставки
        bets_deposits = 0
        bets_withdrawals = 0
        for row in bets_data:
            if len(row) >= 4:  # user_id + 3 поля
                try:
                    row_date = datetime.datetime.strptime(row[1], "%d.%m.%Y").date()  # row[1] - дата
                    if start_date <= row_date <= end_date:
                        operation_type = row[2]  # row[2] - операция
                        amount = float(row[3]) if row[3] else 0  # row[3] - сумма
                        
                        if operation_type == "Пополнение":
                            bets_deposits += amount
                        elif operation_type == "Вывод":
                            bets_withdrawals += amount
                except:
                    continue
        
        total_bets_net = bets_withdrawals - bets_deposits
        
        # Общие расчеты
        total_income_with_tips = total_my_income + total_tips
        total_with_bets = total_income_with_tips + total_bets_net
        balance = total_with_bets - total_expenses
        
        # Форматируем даты для заголовка
        if period_text.startswith("за "):
            date_range = f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        else:
            date_range = start_date.strftime('%d.%m.%Y')
        
        response = (
            f"📊 ОТЧЕТ {period_text.upper()}:\n"
            f"📅 Период: {date_range}\n\n"
            f"💼 Основной доход: {total_my_income:,.0f} ₽\n"
            f"💝 Чаевые/подарки: {total_tips:,.0f} ₽\n"
            f"🎰 Ставки: {total_bets_net:+,.0f} ₽\n"
            f"📤 Расходы: {total_expenses:,.0f} ₽\n"
            f"⚖️ Баланс: {balance:,.0f} ₽\n\n"
            f"📈 Статистика заявок:\n"
            f"🏢 Фирма: {firm_count}\n"
            f"📱 Авито: {avito_count}\n" 
            f"👥 Сарафанка: {sarafanka_count}\n"
            f"🎯 Всего: {firm_count + avito_count + sarafanka_count}"
        )
        
        await message.answer(response, reply_markup=main_kb)
        
    except Exception as e:
        await message.answer("❌ Ошибка формирования отчета")
        logger.error(f"Report error: {e}")

# ========== ОТЧЕТ ФИРМЕ ==========
@router.message(lambda m: m.text == "🏢 Отчет фирме")
async def start_firm_report(message: Message, state: FSMContext):
    await state.set_state(FirmReportStates.period)
    
    # Сразу показываем текущую ситуацию с долгами
    user_id = str(message.from_user.id)
    incomes = sheets_manager.get_user_data(sheets_manager.sheet_income, user_id)
    
    unpaid_requests = []
    total_debt = 0
    firm_count = 0
    
    for row in incomes:
        if len(row) >= 8 and row[2] == "🏢 Фирма":  # row[2] - источник
            try:
                debt = float(row[6]) if row[6] else 0  # row[6] - долг фирме
                if len(row) >= 8 and row[7] == "Не оплачено" and debt > 0:  # row[7] - статус
                    unpaid_requests.append({
                        'date': row[1],  # row[1] - дата
                        'request_number': row[3],  # row[3] - номер заявки
                        'debt': debt
                    })
                    total_debt += debt
                firm_count += 1
            except:
                continue
    
    status_text = (
        f"🏢 ТЕКУЩИЙ ДОЛГ: {total_debt:,.0f} ₽\n"
        f"📋 Неоплаченных заявок: {len(unpaid_requests)}\n"
        f"🔢 Всего заявок фирмы: {firm_count}\n\n"
        f"Выбери период для отчета:"
    )
    
    await message.answer(status_text, reply_markup=firm_report_kb)

@router.message(FirmReportStates.period)
async def generate_firm_report(message: Message, state: FSMContext):
    if await cancel_handler(message, state):
        return
        
    try:
        user_id = str(message.from_user.id)
        incomes = sheets_manager.get_user_data(sheets_manager.sheet_income, user_id)
        
        today = datetime.date.today()
        
        if message.text == "🏢 Неделя фирмы":
            # ПОКАЗЫВАЕМ ТОЛЬКО НЕОПЛАЧЕННЫЕ ЗАЯВКИ ЗА ВЕСЬ ПЕРИОД
            period_text = "неоплаченные"
            show_only_unpaid = True
            date_filter = None
        elif message.text == "🏢 Месяц фирмы":
            start_date = today - datetime.timedelta(days=30)
            period_text = "за месяц"
            show_only_unpaid = False
            date_filter = start_date
        else:  # Год фирмы
            start_date = today - datetime.timedelta(days=365)
            period_text = "за год" 
            show_only_unpaid = False
            date_filter = start_date
        
        # Расчеты для отчета фирме
        firm_repairs = 0
        firm_debt = 0
        firm_count = 0
        firm_requests = []
        
        # Чаевые с заявок фирмы
        firm_tips = 0
        
        for row in incomes:
            if len(row) >= 7 and row[2] == "🏢 Фирма":  # row[2] - источник
                try:
                    row_date = datetime.datetime.strptime(row[1], "%d.%m.%Y").date()  # row[1] - дата
                    
                    # Проверяем фильтр по дате
                    date_ok = True
                    if date_filter and row_date < date_filter:
                        date_ok = False
                    
                    # Проверяем фильтр по оплате
                    payment_ok = True
                    if show_only_unpaid:
                        payment_ok = (len(row) >= 8 and row[7] == "Не оплачено")  # row[7] - статус
                    
                    if date_ok and payment_ok:
                        repair_amount = float(row[4]) if row[4] else 0  # row[4] - сумма чека
                        debt = float(row[6]) if row[6] else 0  # row[6] - долг фирме
                        request_num = row[3] if len(row) > 3 else "?"  # row[3] - номер заявки
                        
                        firm_repairs += repair_amount
                        firm_debt += debt
                        firm_count += 1
                        status = row[7] if len(row) > 7 else "?"  # row[7] - статус
                        firm_requests.append(f"{request_num} - {repair_amount:,.0f} ₽ ({status})")
                except:
                    continue
        
        # Считаем чаевые связанные с заявками фирмы
        tips_data = sheets_manager.get_user_data(sheets_manager.sheet_tips, user_id)
        for row in tips_data:
            if len(row) >= 5:  # user_id + 4 поля
                try:
                    row_date = datetime.datetime.strptime(row[1], "%d.%m.%Y").date()  # row[1] - дата
                    comment = row[4] if len(row) > 4 else ""  # row[4] - комментарий
                    
                    date_ok = True
                    if date_filter and row_date < date_filter:
                        date_ok = False
                    
                    # Если в комментарии есть упоминание фирмы или номера заявки
                    if date_ok and ("Фирма" in comment or any(req.split(' - ')[0] in comment for req in firm_requests if ' - ' in req)):
                        firm_tips += float(row[3]) if row[3] else 0  # row[3] - сумма
                except:
                    continue
        
        my_income_from_firm = firm_repairs - firm_debt
        total_income_with_tips = my_income_from_firm + firm_tips
        
        # Формируем список заявок (максимум 15 штук)
        requests_text = "\n".join(firm_requests[:15])
        if len(firm_requests) > 15:
            requests_text += f"\n... и еще {len(firm_requests) - 15} заявок"
        
        response = (
            f"🏢 ОТЧЕТ ФИРМЕ ({period_text}):\n"
            f"🔧 Заявок: {firm_count}\n"
            f"💵 Общая сумма: {firm_repairs:,.0f} ₽\n"
            f"🏢 Долг фирме: {firm_debt:,.0f} ₽\n"
            f"💸 Мой доход с фирмы: {my_income_from_firm:,.0f} ₽\n"
            f"💝 Чаевые с заявок: {firm_tips:,.0f} ₽\n"
            f"🎯 Итого с чаевыми: {total_income_with_tips:,.0f} ₽\n\n"
        )
        
        if firm_requests:
            response += f"📋 Заявки:\n{requests_text}"
        else:
            response += "📋 Нет заявок по выбранным критериям"
        
        await message.answer(response, reply_markup=main_kb)
        await state.clear()
        
    except Exception as e:
        await message.answer("❌ Ошибка формирования отчета фирме")
        logger.error(f"Firm report error: {e}")

# Обработка кнопки "Назад"
@router.message(lambda m: m.text == "⬅️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_kb)
