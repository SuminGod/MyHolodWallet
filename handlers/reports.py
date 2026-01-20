# handlers/reports.py
import datetime
import logging
import io
import matplotlib.pyplot as plt
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from utils.user_manager import sheets_manager
from keyboards import main_kb, report_kb

router = Router()
logger = logging.getLogger(__name__)

TARGET_MONTHLY_INCOME = 150000

async def get_report_data(user_id, start_date, end_date):
    """Получение и фильтрация данных из таблиц"""
    incomes = sheets_manager.get_user_data(sheets_manager.sheet_income, user_id)
    expenses = sheets_manager.get_user_data(sheets_manager.sheet_expense, user_id)
    
    data = {
        "work_inc": 0, "pers_inc": 0,
        "work_exp": 0, "pers_exp": 0,
        "exp_cats": {}
    }

    # Считаем доходы
    for row in incomes:
        try:
            # Дата в row[0], Тип в row[1], Доход в row[5]
            r_date = datetime.datetime.strptime(row[0], "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                amount = float(row[5])
                if row[1] == "Работа":
                    data["work_inc"] += amount
                else:
                    data["pers_inc"] += amount
        except:
            continue

    # Считаем расходы
    for row in expenses:
        try:
            # Дата в row[0], Тип в row[1], Категория в row[2], Сумма в row[3]
            r_date = datetime.datetime.strptime(row[0], "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                amount = float(row[3])
                cat = row[2]
                if row[1] == "Работа":
                    data["work_exp"] += amount
                else:
                    data["pers_exp"] += amount
                
                data["exp_cats"][cat] = data["exp_cats"].get(cat, 0) + amount
        except:
            continue
        
    return data

def create_charts(data, title):
    """Создание графиков через matplotlib"""
    # Создаем фигуру с двумя графиками
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # 1. Круговая диаграмма расходов
    if data["exp_cats"]:
        ax1.pie(data["exp_cats"].values(), labels=data["exp_cats"].keys(), autopct='%1.1f%%')
        ax1.set_title("Структура расходов")
    else:
        ax1.text(0.5, 0.5, "Нет данных", ha='center')

    # 2. Столбчатая диаграмма (Доходы vs Расходы)
    total_inc = data["work_inc"] + data["pers_inc"]
    total_exp = data["work_exp"] + data["pers_exp"]
    
    ax2.bar(['Доходы', 'Расходы'], [total_inc, total_exp], color=['#4CAF50', '#F44336'])
    ax2.set_title(f"Баланс: {total_inc - total_exp:,.0f} ₽")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
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
        start_date = today - datetime.timedelta(days=7)
        title = "за неделю"
    else:
        start_date = today.replace(day=1)
        title = "за месяц"

    data = await get_report_data(user_id, start_date, today)
    
    # Шкала прогресса к 150к
    total_income = data["work_inc"] + data["pers_inc"]
    percent = min(int((total_income / TARGET_MONTHLY_INCOME) * 100), 100)
    filled = int(percent / 10)
    progress_bar = f"\n\n🎯 Цель 150к: [{'✅'*filled}{'⬜'*(10-filled)}] {percent}%"

    report_text = (
        f"📊 ОТЧЕТ {title.upper()}\n"
        f"--------------------------\n"
        f"🛠 Работа: {data['work_inc']:,.0f} ₽\n"
        f"👤 Личное: {data['pers_inc']:,.0f} ₽\n"
        f"📤 Расходы: {data['work_exp'] + data['pers_exp']:,.0f} ₽\n"
        f"⚖️ Чистыми: {total_income - (data['work_exp'] + data['pers_exp']):,.0f} ₽"
        f"{progress_bar if message.text != '📅 Сегодня' else ''}"
    )

    if message.text in ["📆 Неделя", "🗓️ Месяц"] and data["exp_cats"]:
        chart_buf = create_charts(data, title)
        photo = BufferedInputFile(chart_buf.read(), filename="report.png")
        await message.answer_photo(photo, caption=report_text, reply_markup=main_kb)
    else:
        await message.answer(report_text, reply_markup=main_kb)
