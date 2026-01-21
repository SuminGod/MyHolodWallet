import datetime
import io
import logging
import matplotlib.pyplot as plt
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from utils.user_manager import sheets_manager
from keyboards import main_kb, report_kb

router = Router()
logger = logging.getLogger(__name__) # Добавили логгер
TARGET_MONTHLY_INCOME = 150000

async def get_report_data(user_id, start_date, end_date):
    incomes = sheets_manager.get_user_data(sheets_manager.sheet_income, user_id)
    expenses = sheets_manager.get_user_data(sheets_manager.sheet_expense, user_id)
    tips = sheets_manager.get_user_data(sheets_manager.sheet_tips, user_id)
    
    data = {
        "work_inc": 0, "pers_inc": 0,
        "work_exp": 0, "pers_exp": 0,
        "tips_total": 0, "exp_cats": {}
    }

    def clean_float(val):
        if not val: return 0.0
        try:
            # Очистка от мусора: пробелы, валюта, запятые
            cleaned = str(val).replace(' ', '').replace('₽', '').replace(',', '.').strip()
            return float(cleaned)
        except: 
            return 0.0

    # 1. Доходы (Income)
    for row in incomes:
        try:
            if len(row) < 7: continue
            r_date = datetime.datetime.strptime(row[1].strip(), "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                amount = clean_float(row[6])
                if row[2].strip() == "Работа": data["work_inc"] += amount
                else: data["pers_inc"] += amount
        except: continue

    # 2. ЧАЕВЫЕ (Tips) - Проверка структуры
    for row in tips:
        try:
            # Согласно твоему описанию: A-id(0), B-date(1), C-категория(2), D-сумма(3)
            if len(row) < 4: 
                continue 
            
            r_date_str = row[1].strip()
            r_date = datetime.datetime.strptime(r_date_str, "%d.%m.%Y").date()
            
            if start_date <= r_date <= end_date:
                amount = clean_float(row[3])
                if amount > 0:
                    data["tips_total"] += amount
                    data["work_inc"] += amount
                    # print(f"DEBUG: Нашел чаевые {amount} от {r_date_str}") # Раскомментируй для теста
        except Exception as e:
            # Если дата в другом формате, этот блок поймает ошибку и не даст боту упасть
            continue

    # 3. Расходы (Expense)
    for row in expenses:
        try:
            # Учитываем сдвиг: сумма в E (индекс 4)
            if len(row) < 5: continue
            
            # Проверка на "битую" строку, где вместо даты ID
            date_cell = row[1].strip()
            if len(date_cell) > 10: # Если в дате слишком много цифр (user_id)
                r_date = datetime.datetime.strptime(row[2].strip(), "%d.%m.%Y").date()
                amount = clean_float(row[5]) # Сумма тоже сместилась
                cat = row[4].strip()
                r_type = row[3].strip()
            else:
                r_date = datetime.datetime.strptime(date_cell, "%d.%m.%Y").date()
                amount = clean_float(row[4])
                cat = row[3].strip()
                r_type = row[2].strip()

            if start_date <= r_date <= end_date:
                if r_type == "Работа": data["work_exp"] += amount
                else: data["pers_exp"] += amount
                data["exp_cats"][cat] = data["exp_cats"].get(cat, 0) + amount
        except: continue

    return data

def create_charts(data):
    # Создание графиков
    plt.style.use('ggplot') # Сделаем графики посимпатичнее
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    if data["exp_cats"]:
        ax1.pie(data["exp_cats"].values(), labels=data["exp_cats"].keys(), autopct='%1.1f%%', colors=plt.cm.Paired.colors)
        ax1.set_title("Категории трат")
    
    total_in = data["work_inc"] + data["pers_inc"]
    total_ex = data["work_exp"] + data["pers_exp"]
    ax2.bar(['Доходы', 'Расходы'], [total_in, total_ex], color=['#2ecc71', '#e74c3c'])
    ax2.set_title("Общий баланс")
    
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png'); buf.seek(0); plt.close(fig)
    return buf

@router.message(F.text == "📊 Отчет")
async def show_reports_menu(message: Message):
    await message.answer("За какой период выгрузить данные?", reply_markup=report_kb)

@router.message(F.text.in_(["📅 Сегодня", "📆 Неделя", "🗓️ Месяц"]))
async def handle_report_request(message: Message):
    user_id = str(message.from_user.id)
    today = datetime.date.today()
    
    if message.text == "📅 Сегодня": start_date = today
    elif message.text == "📆 Неделя": start_date = today - datetime.timedelta(days=7)
    else: start_date = today.replace(day=1)
    
    data = await get_report_data(user_id, start_date, today)
    
    total_inc = data["work_inc"] + data["pers_inc"]
    total_exp = data["work_exp"] + data["pers_exp"]
    
    # Расчет прогресса (только работа + чаевые)
    percent = min(int((data["work_inc"] / TARGET_MONTHLY_INCOME) * 100), 100) if TARGET_MONTHLY_INCOME > 0 else 0
    progress = "🔵" * (percent // 10) + "⚪" * (10 - (percent // 10))

    report_text = (
        f"📊 *ФИНАНСОВЫЙ ОТЧЕТ* ({message.text})\n\n"
        f"🛠 *Работа:* {data['work_inc']:,.0f} ₽\n"
        f"└ _в т.ч. чаевые:_ {data['tips_total']:,.0f} ₽\n"
        f"👤 *Личное:* {data['pers_inc']:,.0f} ₽\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"🔻 *Всего расходов:* {total_exp:,.0f} ₽\n"
        f"💰 *Чистая прибыль:* {total_inc - total_exp:,.0f} ₽\n\n"
        f"🎯 *Цель месяца:* {TARGET_MONTHLY_INCOME:,.0f} ₽\n"
        f"[{progress}] {percent}%"
    )

    if message.text != "📅 Сегодня" and (total_inc > 0 or total_exp > 0):
        chart_data = create_charts(data)
        photo = BufferedInputFile(chart_data.read(), filename="report.png")
        await message.answer_photo(photo, caption=report_text, parse_mode="Markdown")
    else:
        await message.answer(report_text, parse_mode="Markdown")
