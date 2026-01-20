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
    # Получаем данные пользователя из таблиц
    incomes = sheets_manager.get_user_data(sheets_manager.sheet_income, user_id)
    expenses = sheets_manager.get_user_data(sheets_manager.sheet_expense, user_id)
    
    data = {
        "work_inc": 0, "pers_inc": 0,
        "work_exp": 0, "pers_exp": 0,
        "exp_cats": {}
    }

    # ОБРАБОТКА ДОХОДОВ
    # Структура: ID(0), Дата(1), Тип(2), Кат(3), №(4), Чек(5), Доход(6)
    for row in incomes:
        try:
            if len(row) < 7: continue
            r_date = datetime.datetime.strptime(row[1].strip(), "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                r_type = row[2].strip()
                # Сумма дохода теперь в индексе 6
                amount = float(str(row[6]).replace(',', '.').replace(' ', ''))
                
                if r_type == "Работа":
                    data["work_inc"] += amount
                else:
                    data["pers_inc"] += amount
        except Exception as e:
            logger.warning(f"Ошибка в строке дохода: {e}")
            continue

    # ОБРАБОТКА РАСХОДОВ
    # Структура: ID(0), Дата(1), Тип(2), Кат(3), Сумма(4)
    for row in expenses:
        try:
            if len(row) < 5: continue
            r_date = datetime.datetime.strptime(row[1].strip(), "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                r_type = row[2].strip()
                cat = row[3].strip()
                # Сумма расхода теперь в индексе 4
                amount = float(str(row[4]).replace(',', '.').replace(' ', ''))
                
                if r_type == "Работа":
                    data["work_exp"] += amount
                else:
                    data["pers_exp"] += amount
                
                data["exp_cats"][cat] = data["exp_cats"].get(cat, 0) + amount
        except Exception as e:
            logger.warning(f"Ошибка в строке расхода: {e}")
            continue
        
    return data

def create_charts(data, title):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Расходы
    if data["exp_cats"]:
        ax1.pie(data["exp_cats"].values(), labels=data["exp_cats"].keys(), autopct='%1.1f%%', startangle=140)
        ax1.set_title("Анализ расходов")
    else:
        ax1.text(0.5, 0.5, "Нет расходов", ha='center')

    # Баланс
    total_in = data["work_inc"] + data["pers_inc"]
    total_out = data["work_exp"] + data["pers_exp"]
    ax2.bar(['Доход', 'Расход'], [total_in, total_out], color=['#2ecc71', '#e74c3c'])
    ax2.set_title(f"Баланс: {total_in - total_out:,.0f} ₽")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf

@router.message(F.text == "📊 Отчет")
async def show_reports_menu(message: Message):
    await message.answer("Выберите период:", reply_markup=report_kb)

@router.message(F.text.in_(["📅 Сегодня", "📆 Неделя", "🗓️ Месяц"]))
async def handle_report_request(message: Message):
    user_id = str(message.from_user.id)
    today = datetime.date.today()
    
    if message.text == "📅 Сегодня":
        start_date = today
        title = "сегодня"
    elif message.text == "📆 Неделя":
        start_date = today - datetime.timedelta(days=7)
        title = "неделю"
    else:
        start_date = today.replace(day=1)
        title = "месяц"

    data = await get_report_data(user_id, start_date, today)
    
    total_income = data["work_inc"] + data["pers_inc"]
    percent = min(int((total_income / TARGET_MONTHLY_INCOME) * 100), 100)
    filled = int(percent / 10)
    progress_bar = f"\n\n🎯 Цель 150к: [{'🔵'*filled}{'⚪'*(10-filled)}] {percent}%"

    report_text = (
        f"📊 ОТЧЕТ ЗА {title.upper()}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🛠 Работа:  {data['work_inc']:,.0f} ₽\n"
        f"👤 Личное:  {data['pers_inc']:,.0f} ₽\n"
        f"🔻 Расходы: {data['work_exp'] + data['pers_exp']:,.0f} ₽\n"
        f"━━━━━━━━━━━━━━\n"
        f"💰 ИТОГО:   {total_income - (data['work_exp'] + data['pers_exp']):,.0f} ₽"
        f"{progress_bar if message.text != '📅 Сегодня' else ''}"
    )

    if message.text in ["📆 Неделя", "🗓️ Месяц"] and (data["work_inc"] > 0 or data["work_exp"] > 0):
        chart_buf = create_charts(data, title)
        photo = BufferedInputFile(chart_buf.read(), filename="report.png")
        await message.answer_photo(photo, caption=report_text, reply_markup=main_kb)
    else:
        await message.answer(report_text, reply_markup=main_kb)
