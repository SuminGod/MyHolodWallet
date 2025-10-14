# keyboards.py
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="💵 Добавить доход"))
    builder.add(KeyboardButton(text="💰 Чаевые"))
    builder.add(KeyboardButton(text="📤 Добавить расход"))
    builder.add(KeyboardButton(text="📊 Отчет"))
    builder.add(KeyboardButton(text="🎯 Ставки"))
    builder.add(KeyboardButton(text="💳 Отметить оплату фирме")) 
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_income_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🏢 Фирма"))
    builder.add(KeyboardButton(text="📱 Авито")) 
    builder.add(KeyboardButton(text="👥 Сарафанка"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_tips_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="💵 Чаевые наличные"))
    builder.add(KeyboardButton(text="💳 Чаевые перевод"))
    builder.add(KeyboardButton(text="🎁 Подарок"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_expense_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🔧 Детали"))
    builder.add(KeyboardButton(text="🚗 Авто"))
    builder.add(KeyboardButton(text="📢 Реклама"))
    builder.add(KeyboardButton(text="🍕 Еда"))
    builder.add(KeyboardButton(text="🏠 Квартира"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(3, 3)
    return builder.as_markup(resize_keyboard=True)

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
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)
def get_bets_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="💰 Пополнение"))
    builder.add(KeyboardButton(text="💸 Вывод"))
    builder.add(KeyboardButton(text="📊 Отчет ставок"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_bets_report_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🎯 День ставок"))
    builder.add(KeyboardButton(text="🎯 Неделя ставок"))
    builder.add(KeyboardButton(text="🎯 Месяц ставок"))
    builder.add(KeyboardButton(text="🎯 Год ставок"))
    builder.add(KeyboardButton(text="⬅️ Назад"))
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

# Присваиваем клавиатуры
main_kb = get_main_kb()
income_kb = get_income_kb()
tips_kb = get_tips_kb()
expense_kb = get_expense_kb()
report_kb = get_report_kb()
firm_report_kb = get_firm_report_kb()
bets_kb = get_bets_kb()
bets_report_kb = get_bets_report_kb()


# Добавляем в существующие клавиатуры


# Обновляем список клавиатур в конце файла

