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
async def show_reports(message: Message):# handlers/reports.py
import datetime
import logging
import io
import matplotlib.pyplot as plt
import pandas as pd
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from utils.user_manager import sheets_manager
from keyboards import main_kb, report_kb

router = Router()
logger = logging.getLogger(__name__)

TARGET_MONTHLY_INCOME = 150000

# Вспомогательная функция для получения данных
async def get_report_data(user_id, start_date, end_date):
    incomes = sheets_manager.get_user_data(sheets_manager.sheet_income, user_id)
    expenses = sheets_manager.get_user_data(sheets_manager.sheet_expense, user_id)
    
    data = {
        "work_inc": 0, "pers_inc": 0,
        "work_exp": 0, "pers_exp": 0,
        "exp_cats": {}, "daily_stats": {}
    }

    # Обработка доходов
    for row in incomes:
        try:
            r_date = datetime.datetime.strptime(row[0], "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                amount = float(row[5])
                if row[1] == "Работа": data["work_inc"] += amount
                else: data["pers_inc"] += amount
        except: continue

    # Обработка расходов
    for row in expenses:
        try:
            r_date = datetime.datetime.strptime(row[0], "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                amount = float(row[3])
                cat = row[2]
                if row[1] == "Работа": data["work_exp"] += amount
                else: data["pers_exp"] += amount
                
                data["exp_cats"][cat] = data["exp_cats"].get(cat, 0) + amount
        except: continue
        
    return data

# Функция генерации графиков
def create_charts(data, title):
    plt.figure(figsize=(10, 6))
    
    # 1. Круговая диаграмма расходов
    if data["exp_cats"]:
        plt.subplot(1, 2, 1)
        plt.pie(data["exp_cats"].values(), labels=data["exp_cats"].keys(), autopct='%1.1f%%')
        plt.title("Структура расходов")

    # 2. Столбцы Доход vs Расход
    plt.subplot(1, 2, 2)
    labels = ['Доходы', 'Расходы']
    values = [data["work_inc"] + data["pers_inc"], data["work_exp"] + data["pers_exp"]]
    plt.bar(labels, values, color=['green', 'red'])
    plt.title(f"Баланс: {values[0]-values[1]:,.0f} ₽")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

@router.message(F.text == "📊 Отчет")
async def show_reports_menu(message: Message):
    await message.answer("Выберите период отчета:", reply_markup=report_kb)

@router.message(F.text.in_(["📅 Сегодня", "📆 Неделя", "🗓️ Месяц"]))
async def handle_report_request(message: Message):
    user_id = str(message.from_user.id)
    today = datetime.date.today()
    
    if message.text == "📅 Сегодня":
        start_date = today
        title = "за сегодня"
    elif message.text == "📆 Неделя":
        start_date = today - datetime.timedelta(days=today.weekday())
        title = "за неделю"
    else:
        start_date = today.replace(day=1)
        title = "за месяц"

    data = await get_report_data(user_id, start_date, today)
    
    # Шкала прогресса (только для месяца)
    progress_bar = ""
    if message.text in ["🗓️ Месяц", "📈 Год"]:
        total_inc = data["work_inc"] + data["pers_inc"]
        percent = min(int((total_inc / TARGET_MONTHLY_INCOME) * 100), 100)
        filled = int(percent / 10)
        progress_bar = f"\n\n🎯 Цель 150к: [{'✅'*filled}{'⬜'*(10-filled)}] {percent}%"

    report_text = (
        f"📊 ОТЧЕТ {title.upper()}\n"
        f"--------------------------\n"
        f"🛠 Работа: {data['work_inc']:,.0f} ₽\n"
        f"👤 Личное: {data['pers_inc']:,.0f} ₽\n"
        f"📤 Расходы: {data['work_exp'] + data['pers_expense']:,.0f} ₽\n"
        f"⚖️ Чистыми: {(data['work_inc'] + data['pers_inc']) - (data['work_exp'] + data['pers_exp']):,.0f} ₽"
        f"{progress_bar}"
    )

    if message.text in ["📆 Неделя", "🗓️ Месяц"]:
        chart_buf = create_charts(data, title)
        photo = BufferedInputFile(chart_buf.read(), filename="report.png")
        await message.answer_photo(photo, caption=report_text, reply_markup=main_kb)
    else:
        await message.answer(report_text, reply_markup=main_kb)
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

