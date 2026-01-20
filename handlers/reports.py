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
    data = {"work_inc": 0, "pers_inc": 0, "work_exp": 0, "pers_exp": 0, "exp_cats": {}}

    for row in incomes:
        try:
            if len(row) < 7: continue
            r_date = datetime.datetime.strptime(row[1].strip(), "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                amount = float(str(row[6]).replace(',', '.').replace(' ', ''))
                if row[2].strip() == "Работа": data["work_inc"] += amount
                else: data["pers_inc"] += amount
        except: continue

    for row in expenses:
        try:
            if len(row) < 5: continue
            r_date = datetime.datetime.strptime(row[1].strip(), "%d.%m.%Y").date()
            if start_date <= r_date <= end_date:
                # ИНДЕКС 4 — Столбец E (Сумма)
                amount = float(str(row[4]).replace(',', '.').replace(' ', ''))
                cat = row[3].strip()
                if row[2].strip() == "Работа": data["work_exp"] += amount
                else: data["pers_exp"] += amount
                data["exp_cats"][cat] = data["exp_cats"].get(cat, 0) + amount
        except: continue
    return data

def create_charts(data):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    if data["exp_cats"]:
        ax1.pie(data["exp_cats"].values(), labels=data["exp_cats"].keys(), autopct='%1.1f%%')
    ax2.bar(['Доход', 'Расход'], [data["work_inc"]+data["pers_inc"], data["work_exp"]+data["pers_exp"]], color=['green', 'red'])
    buf = io.BytesIO()
    plt.savefig(buf, format='png'); buf.seek(0); plt.close(fig)
    return buf

@router.message(F.text == "📊 Отчет")
async def show_reports_menu(message: Message):
    await message.answer("Выберите период:", reply_markup=report_kb)

@router.message(F.text.in_(["📅 Сегодня", "📆 Неделя", "🗓️ Месяц"]))
async def handle_report_request(message: Message):
    user_id = str(message.from_user.id)
    today = datetime.date.today()
    start_date = today if message.text == "📅 Сегодня" else (today - datetime.timedelta(days=7) if message.text == "📆 Неделя" else today.replace(day=1))
    
    data = await get_report_data(user_id, start_date, today)
    total_inc = data["work_inc"] + data["pers_inc"]
    percent = min(int((total_inc / TARGET_MONTHLY_INCOME) * 100), 100)
    
    report_text = (f"📊 ОТЧЕТ\n🛠 Работа: {data['work_inc']:,.0f} ₽\n👤 Личное: {data['pers_inc']:,.0f} ₽\n"
                   f"🔻 Расходы: {data['work_exp']+data['pers_exp']:,.0f} ₽\n🎯 Цель 150к: [{'🔵'*(percent//10)}{'⚪'*(10-(percent//10))}] {percent}%")

    if message.text != "📅 Сегодня" and (total_inc > 0 or sum(data["exp_cats"].values()) > 0):
        photo = BufferedInputFile(create_charts(data).read(), filename="report.png")
        await message.answer_photo(photo, caption=report_text, reply_markup=main_kb)
    else:
        await message.answer(report_text, reply_markup=main_kb)
