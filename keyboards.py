# keyboards.py
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- ГЛАВНОЕ МЕНЮ ---
def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="💰 Доход"))
    builder.add(KeyboardButton(text="📤 Расход"))
    builder.add(KeyboardButton(text="❄️ Работа"))
    builder.add(KeyboardButton(text="📉 Долги/Кредиты"))
    builder.add(KeyboardButton(text="📊 Отчет"))
    builder.add(KeyboardButton(text="🗑️ Удалить записи"))
    builder.adjust(2, 1, 2, 1)
    return builder.as_markup(resize_keyboard=True)

# --- ДОХОДЫ (ЛИЧНЫЕ) ---
def get_income_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="💵 Зарплата"))
    builder.add(KeyboardButton(text="🎁 Подарок"))
    builder.add(KeyboardButton(text="📈 Кэшбэк"))
    builder.add(KeyboardButton(text="📦 Продажа вещей"))
    builder.add(KeyboardButton(text="🔄 Прочее"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup(resize_keyboard=True)

# --- РАСХОДЫ (ЛИЧНЫЕ) ---
def get_expense_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🍕 Еда"))
    builder.add(KeyboardButton(text="🏠 Жилье"))
    builder.add(KeyboardButton(text="💊 Здоровье"))
    builder.add(KeyboardButton(text="🧼 Хозтовары"))
    builder.add(KeyboardButton(text="🚌 Транспорт"))
    builder.add(KeyboardButton(text="📱 Связь"))
    builder.add(KeyboardButton(text="👕 Одежда"))
    builder.add(KeyboardButton(text="🎭 Досуг"))
    builder.add(KeyboardButton(text="🎓 Обучение"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(3, 3, 3, 1)
    return builder.as_markup(resize_keyboard=True)

# --- РАБОТА (ХОЛОДИЛЬЩИК) ---
def get_work_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🏢 Фирма"))
    builder.add(KeyboardButton(text="📱 Авито")) 
    builder.add(KeyboardButton(text="👥 Сарафанка"))
    builder.add(KeyboardButton(text="🔧 Расход (Работа)"))
    builder.add(KeyboardButton(text="💳 Отметить оплату фирме"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(3, 1, 1, 1)
    return builder.as_markup(resize_keyboard=True)

# --- ДОЛГИ И КРЕДИТЫ ---
def get_debt_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📊 Список долгов"))
    builder.add(KeyboardButton(text="💸 Внести платеж"))
    builder.add(KeyboardButton(text="➕ Добавить долг"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup(resize_keyboard=True)

# --- ОТЧЕТЫ ---
def get_report_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📅 Сегодня"))
    builder.add(KeyboardButton(text="📆 Неделя"))
    builder.add(KeyboardButton(text="🗓️ Месяц"))
    builder.add(KeyboardButton(text="📈 Год"))
    builder.add(KeyboardButton(text="🏢 Отчет фирме"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_firm_report_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🏢 Неделя фирмы"))
    builder.add(KeyboardButton(text="🏢 Месяц фирмы")) 
    builder.add(KeyboardButton(text="🏢 Год фирмы"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2, 1)
    return builder.as_markup(resize_keyboard=True)

# --- ИНИЦИАЛИЗАЦИЯ (Экспорт для других файлов) ---
# Это решит проблему "cannot import name 'report_kb'"
main_kb = get_main_kb()
income_kb = get_income_kb()
expense_kb = get_expense_kb()
work_kb = get_work_kb()
debt_kb = get_debt_kb()
report_kb = get_report_kb()
firm_report_kb = get_firm_report_kb()
