import datetime
import io
import matplotlib.pyplot as plt
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from utils.user_manager import sheets_manager
from keyboards import main_kb, report_kb

router = Router()

# Ваша цель по доходу
TARGET_MONTHLY_INCOME = 150000

async def get_report_data(user_id, start_date, end_date):
    # Загружаем данные из всех необходимых листов
    incomes = sheets_manager.get_user_data(sheets_manager.sheet_income, user_id)
    expenses = sheets_manager.get_user_data(sheets_manager.sheet_expense, user_id)
    tips = sheets_manager.get_user_data(sheets_manager.sheet_tips, user_id)
    
    data = {
        "work_inc": 0,      # Доход по работе
        "pers_inc": 0,      # Личный доход
        "work_exp": 0,      # Расходы по работе
        "pers_exp": 0,      # Личные расходы
        "tips_total": 0,    # Чаевые отдельно (для текста)
        "exp_cats": {}      # Категории расходов для графика
    }

    # 1. ОБРАБОТКА ОСНОВНЫХ ДОХОДОВ (Income)
    for row in incomes:
        try:
            if len(row) < 7: continue
            r_date = datetime.datetime.strptime(row[1].strip(), "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                amount = float(str(row[6]).replace(',', '.').replace(' ', ''))
                if row[2].strip() == "Работа":
                    data["work_inc"] += amount
                else:
                    data["pers_inc"] += amount
        except: continue

    # 2. ОБРАБОТКА ЧАЕВЫХ (Tips) - добавляем их к рабочему доходу
    for row in tips:
        try:
            if len(row) < 3: continue
            r_date = datetime.datetime.strptime(row[1].strip(), "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                tip_amount = float(str(row[2]).replace(',', '.').replace(' ', ''))
                data["tips_total"] += tip_amount
                data["work_inc"] += tip_amount # Чаевые идут в общий кошелек работы
        except: continue

    # 3. ОБРАБОТКА РАСХОДОВ (Expense)
    for row in expenses:
        try:
            if len(row) < 5: continue
            r_date = datetime.datetime.strptime(row[1].strip(), "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                # Индекс 4 — это столбец E (Сумма)
                amount = float(str(row[4]).replace(',', '.').replace(' ', ''))
                cat = row[3].strip()
                
                if row[2].strip() == "Работа":
                    data["work_exp"] += amount
                else:
                    data["pers_exp"] += amount
                
                # Собираем статистику по категориям для круговой диаграммы
                data["exp_cats"][cat] = data["exp_cats"].get(cat, 0) + amount
        except: continue

    return data

def create_charts(data):
    # Создаем два графика: категории расходов и доходы vs расходы
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Левый график: Категории расходов
    if data["exp_cats"]:
        ax1.pie(data["exp_cats"].values(), labels=data["exp_cats"].keys(), autopct='%1.1f%%', startangle=140)
        ax1.set_title("Расходы по категориям")
    else:
        ax1.text(0.5, 0.5, "Нет данных по расходам", ha='center')

    # Правый график: Доходы и Расходы
    total_in = data["work_inc"] + data["pers_inc"]
    total_ex = data["work_exp"] + data["pers_exp"]
    ax2.bar(['Доход', 'Расход'], [total_in, total_ex], color=['#2ecc71', '#e74c3c'])
    ax2.set_title("Баланс за период")

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf

@router.message(F.text == "📊 Отчет")
async def show_reports_menu(message: Message):
    await message.answer("Выберите период для формирования отчета:", reply_markup=report_kb)

@router.message(F.text.in_(["📅 Сегодня", "📆 Неделя", "🗓️ Месяц"]))
async def handle_report_request(message: Message):
    user_id = str(message.from_user.id)
    today = datetime.date.today()
    
    # Определяем дату начала периода
    if message.text == "📅 Сегодня":
        start_date = today
    elif message.text == "📆 Неделя":
        start_date = today - datetime.timedelta(days=7)
    else: # Месяц
        start_date = today.replace(day=1)
    
    data = await get_report_data(user_id, start_date, today)
    
    total_income = data["work_inc"] + data["pers_inc"]
    total_expense = data["work_exp"] + data["pers_exp"]
    
    # Считаем процент выполнения цели (только для работы)
    percent = min(int((data["work_inc"] / TARGET_MONTHLY_INCOME) * 100), 100)
    progress_bar = "🔵" * (percent // 10) + "⚪" * (10 - (percent // 10))

    report_text = (
        f"📊 *ОТЧЕТ ЗА ПЕРИОД* ({message.text})\n\n"
        f"🛠 *Работа:* {data['work_inc']:,.0f} ₽\n"
        f"└ _в т.ч. чаевые:_ {data['tips_total']:,.0f} ₽\n"
        f"👤 *Личное:* {data['pers_inc']:,.0f} ₽\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"🔻 *Всего расходов:* {total_expense:,.0f} ₽\n"
        f"💰 *Чистая прибыль:* {total_income - total_expense:,.0f} ₽\n\n"
        f"🎯 *Цель (доход работа):* {TARGET_MONTHLY_INCOME:,.0f} ₽\n"
        f"[{progress_bar}] {percent}%"
    )

    # Если есть данные для графиков (кроме отчета за сегодня, там графики часто не нужны)
    if message.text != "📅 Сегодня" and (total_income > 0 or total_expense > 0):
        chart_buffer = create_charts(data)
        photo = BufferedInputFile(chart_buffer.read(), filename="report.png")
        await message.answer_photo(photo, caption=report_text, parse_mode="Markdown", reply_markup=main_kb)
    else:
        await message.answer(report_text, parse_mode="Markdown", reply_markup=main_kb)
