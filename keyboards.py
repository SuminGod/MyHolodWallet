# keyboards.py
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="💰 Доход"))
    builder.add(KeyboardButton(text="📤 Расход"))
    builder.add(KeyboardButton(text="❄️ Работа"))
    builder.add(KeyboardButton(text="📉 Долги/Кредиты"))
    builder.add(KeyboardButton(text="📊 Отчет"))
    builder.add(KeyboardButton(text="🗑️ Удалить"))
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_income_kb():
    builder = ReplyKeyboardBuilder()
    categories = ["💰 Зарплата", "🎁 Подарок", "📈 Кэшбэк", "📦 Продажа вещей", "🔄 Прочее", "⬅️ Назад"]
    for cat in categories:
        builder.add(KeyboardButton(text=cat))
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_expense_kb():
    builder = ReplyKeyboardBuilder()
    # Разделяем на группы для удобства
    cats = ["🍕 Еда", "🏠 Жилье", "💊 Здоровье", "🧼 Хозтовары", "🚌 Транспорт", "📱 Связь", "👕 Одежда", "🎭 Досуг", "🎓 Обучение", "⬅️ Назад"]
    for cat in cats:
        builder.add(KeyboardButton(text=cat))
    builder.adjust(3, 3, 3, 1)
    return builder.as_markup(resize_keyboard=True)

def get_work_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🏢 Фирма"))
    builder.add(KeyboardButton(text="📱 Авито"))
    builder.add(KeyboardButton(text="👥 Сарафанка"))
    builder.add(KeyboardButton(text="🔧 Расход (Работа)"))
    builder.add(KeyboardButton(text="💳 Оплата фирме"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(3, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_debt_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📊 Список долгов"))
    builder.add(KeyboardButton(text="💸 Внести платеж"))
    builder.add(KeyboardButton(text="➕ Добавить долг"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(1, 2, 1)
    return builder.as_markup(resize_keyboard=True)

# Инициализация
main_kb = get_main_kb()
income_kb = get_income_kb()
expense_kb = get_expense_kb()
work_kb = get_work_kb()
debt_kb = get_debt_kb()
report_kb = get_report_kb() # ТА САМАЯ СТРОЧКА, КОТОРОЙ НЕ ХВАТАЛО
firm_report_kb = get_firm_report_kb()

