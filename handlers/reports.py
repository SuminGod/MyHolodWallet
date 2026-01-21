import datetime
import io
import matplotlib.pyplot as plt
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from utils.user_manager import sheets_manager
from keyboards import main_kb, report_kb

router = Router()
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

    # Помогатор для очистки чисел
    def clean_float(val):
        try:
            return float(str(val).replace(',', '.').replace(' ', '').replace('₽', '').strip())
        except: return 0.0

    # 1. Доходы
    for row in incomes:
        try:
            if len(row) < 7: continue
            r_date = datetime.datetime.strptime(row[1].strip(), "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                amount = clean_float(row[6])
                if row[2].strip() == "Работа": data["work_inc"] += amount
                else: data["pers_inc"] += amount
        except: continue

    for row in tips:
        try:
            # Проверяем, что в строке хватает столбцов (минимум до D)
            if len(row) < 4: continue 
            
            r_date = datetime.datetime.strptime(row[1].strip(), "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                # Берем сумму из столбца D (индекс 3)
                amount = clean_float(row[3]) 
                
                data["tips_total"] += amount
                data["work_inc"] += amount # Плюсуем к рабочему доходу
        except Exception as e:
            logger.error(f"Ошибка парсинга строки чаевых: {e}")
            continue

    # 3. Расходы (Учитываем смещение столбцов E=4)
    for row in expenses:
        try:
            if len(row) < 5: continue
            r_date = datetime.datetime.strptime(row[1].strip(), "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                amount = clean_float(row[4])
                cat = row[3].strip()
                if row[2].strip() == "Работа": data["work_exp"] += amount
                else: data["pers_exp"] += amount
                data["exp_cats"][cat] = data["exp_cats"].get(cat, 0) + amount
        except: continue

    return data

# Функция создания графиков (без изменений)
def create_charts(data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    if data["exp_cats"]:
        ax1.pie(data["exp_cats"].values(), labels=data["exp_cats"].keys(), autopct='%1.1f%%')
    total_in = data["work_inc"] + data["pers_inc"]
    total_ex = data["work_exp"] + data["pers_exp"]
    ax2.bar(['Доход', 'Расход'], [total_in, total_ex], color=['#2ecc71', '#e74c3c'])
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png'); buf.seek(0); plt.close(fig)
    return buf

@router.message(F.text == "📊 Отчет")
async def show_reports_menu(message: Message):
    await message.answer("Выберите период:", reply_markup=report_kb)

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
    percent = min(int((data["work_inc"] / TARGET_MONTHLY_INCOME) * 100), 100)
    progress = "🔵" * (percent // 10) + "⚪" * (10 - (percent // 10))

    report_text = (
        f"📊 *ОТЧЕТ ЗА ПЕРИОД* ({message.text})\n\n"
        f"🛠 *Работа:* {data['work_inc']:,.0f} ₽\n"
        f"└ _в т.ч. чаевые:_ {data['tips_total']:,.0f} ₽\n"
        f"👤 *Личное:* {data['pers_inc']:,.0f} ₽\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"🔻 *Всего расходов:* {total_exp:,.0f} ₽\n"
        f"💰 *Чистая прибыль:* {total_inc - total_exp:,.0f} ₽\n\n"
        f"🎯 *Цель (доход работа):* {TARGET_MONTHLY_INCOME:,.0f} ₽\n"
        f"[{progress}] {percent}%"
    )

    if message.text != "📅 Сегодня" and (total_inc > 0 or total_exp > 0):
        photo = BufferedInputFile(create_charts(data).read(), filename="report.png")
        await message.answer_photo(photo, caption=report_text, parse_mode="Markdown")
    else:
        await message.answer(report_text, parse_mode="Markdown")

