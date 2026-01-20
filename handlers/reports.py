# handlers/reports.py
import datetime
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.user_manager import sheets_manager
from keyboards import main_kb, report_kb

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.text == "📊 Отчет")
async def show_reports(message: Message):
    await message.answer("Какой отчет подготовить?", reply_markup=report_kb)

@router.message(F.text.in_(["📅 Сегодня", "📆 Неделя", "🗓️ Месяц", "📈 Год"]))
async def generate_combined_report(message: Message):
    try:
        user_id = str(message.from_user.id)
        period = message.text
        
        # Определяем даты
        today = datetime.date.today()
        if period == "📅 Сегодня": start_date = today
        elif period == "📆 Неделя": start_date = today - datetime.timedelta(days=7)
        elif period == "📈 Год": start_date = today - datetime.timedelta(days=365)
        else: start_date = today - datetime.timedelta(days=30)
        
        # Загружаем данные
        incomes = sheets_manager.get_user_data(sheets_manager.sheet_income, user_id)
        expenses = sheets_manager.get_user_data(sheets_manager.sheet_expense, user_id)
        
        stats = {
            "work_income": 0, "pers_income": 0,
            "work_expense": 0, "pers_expense": 0,
            "debt_to_firm": 0
        }

        # Считаем Доходы (Дата в row[0], Тип в row[1], Доход в row[5], Долг в row[6])
        for row in incomes:
            try:
                row_date = datetime.datetime.strptime(row[0], "%d.%m.%Y").date()
                if start_date <= row_date <= today:
                    amount = float(row[5])
                    if row[1] == "Работа":
                        stats["work_income"] += amount
                        stats["debt_to_firm"] += float(row[6])
                    else:
                        stats["pers_income"] += amount
            except: continue

        # Считаем Расходы (Дата в row[0], Тип в row[1], Сумма в row[3])
        for row in expenses:
            try:
                row_date = datetime.datetime.strptime(row[0], "%d.%m.%Y").date()
                if start_date <= row_date <= today:
                    amount = float(row[3])
                    if row[1] == "Работа": stats["work_expense"] += amount
                    else: stats["pers_expense"] += amount
            except: continue

        # Формируем текст
        report_text = (
            f"📊 ОТЧЕТ {period.upper()}\n"
            f"--------------------------\n"
            f"🛠 РАБОТА:\n"
            f"   Доход: {stats['work_income']:,.0f} ₽\n"
            f"   Расходы: {stats['work_expense']:,.0f} ₽\n"
            f"   Чистыми: {stats['work_income'] - stats['work_expense']:,.0f} ₽\n"
            f"   Долг фирме: {stats['debt_to_firm']:,.0f} ₽\n\n"
            f"👤 ЛИЧНОЕ:\n"
            f"   Доход: {stats['pers_income']:,.0f} ₽\n"
            f"   Расходы: {stats['pers_expense']:,.0f} ₽\n"
            f"--------------------------\n"
            f"💰 ОБЩИЙ БАЛАНС: { (stats['work_income'] + stats['pers_income']) - (stats['work_expense'] + stats['pers_expense']) :,.0f} ₽"
        )
        
        await message.answer(report_text, reply_markup=main_kb)
        
    except Exception as e:
        logger.error(f"Error in report: {e}")
        await message.answer("❌ Ошибка при расчете отчета.")
