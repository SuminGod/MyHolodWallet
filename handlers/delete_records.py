# handlers/delete_records.py
import datetime
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from keyboards import main_kb
from utils.user_manager import sheets_manager

router = Router()

class DeleteStates(StatesGroup):
    select_category = State()
    select_record = State()

# ========== УДАЛЕНИЕ ЗАПИСЕЙ ==========
@router.message(lambda m: m.text == "🗑️ Удалить записи")
async def delete_records_start(message: Message, state: FSMContext):
    await state.set_state(DeleteStates.select_category)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="💵 Доходы", callback_data="delete_income"))
    keyboard.add(InlineKeyboardButton(text="📤 Расходы", callback_data="delete_expense"))
    keyboard.add(InlineKeyboardButton(text="💰 Чаевые", callback_data="delete_tips"))
    keyboard.add(InlineKeyboardButton(text="🎯 Ставки", callback_data="delete_bets"))
    keyboard.add(InlineKeyboardButton(text="❌ Отмена", callback_data="delete_cancel"))
    keyboard.adjust(2, 2, 1)
    
    await message.answer(
        "🗑️ Выбери категорию для удаления записей:",
        reply_markup=keyboard.as_markup()
    )

@router.callback_query(lambda c: c.data.startswith('delete_') and c.data != 'delete_cancel')
async def process_category_selection(callback: CallbackQuery, state: FSMContext):
    category = callback.data.replace('delete_', '')
    await state.update_data(category=category)
    
    user_id = str(callback.from_user.id)
    
    # Получаем последние записи пользователя
    records = await get_user_records(user_id, category)
    
    if not records:
        await callback.message.edit_text(
            "❌ В этой категории нет записей для удаления\n\n"
            "🏠 Возврат в главное меню",
            reply_markup=None
        )
        await callback.message.answer("Главное меню:", reply_markup=main_kb)
        await state.clear()
        return
    
    await state.update_data(records=records)
    await show_records_for_deletion(callback, records, category)

async def get_user_records(user_id: str, category: str):
    """Получить записи пользователя для указанной категории"""
    try:
        if category == "income":
            sheet = sheets_manager.sheet_income
            all_data = sheets_manager.get_all_data(sheet)
            user_records = []
            for i, row in enumerate(all_data, start=1):
                if len(row) > 0 and row[0] == user_id:
                    # Формируем информативный текст для отображения
                    date = row[1] if len(row) > 1 else ''
                    source = row[2] if len(row) > 2 else ''
                    request_number = row[3] if len(row) > 3 else ''
                    repair_amount = row[4] if len(row) > 4 else '0'
                    my_income = row[5] if len(row) > 5 else '0'
                    debt = row[6] if len(row) > 6 else '0'
                    
                    # Для разных источников показываем разную информацию
                    if source == "🏢 Фирма":
                        display_text = f"{date} - {source} - Заявка {request_number} - Чек: {repair_amount}₽ - Доход: {my_income}₽ - Долг: {debt}₽"
                    else:
                        # Для Авито/Сарафанки показываем личный доход (вся сумма)
                        display_text = f"{date} - {source} - Доход: {my_income}₽"
                    
                    user_records.append({
                        'row_index': i,
                        'date': date,
                        'source': source,
                        'request_number': request_number,
                        'repair_amount': repair_amount,
                        'my_income': my_income,
                        'debt': debt,
                        'display_text': display_text
                    })
            return user_records[-10:]  # Последние 10 записей
        
        elif category == "expense":
            sheet = sheets_manager.sheet_expense
            all_data = sheets_manager.get_all_data(sheet)
            user_records = []
            for i, row in enumerate(all_data, start=1):
                if len(row) > 0 and row[0] == user_id:
                    date = row[1] if len(row) > 1 else ''
                    category_expense = row[2] if len(row) > 2 else ''
                    amount = row[3] if len(row) > 3 else '0'
                    comment = row[4] if len(row) > 4 else ''
                    
                    display_text = f"{date} - {category_expense} - {amount}₽"
                    if comment:
                        display_text += f" - {comment}"
                    
                    user_records.append({
                        'row_index': i,
                        'date': date,
                        'category': category_expense,
                        'amount': amount,
                        'comment': comment,
                        'display_text': display_text
                    })
            return user_records[-10:]  # Последние 10 записей
        
        elif category == "tips":
            sheet = sheets_manager.sheet_tips
            all_data = sheets_manager.get_all_data(sheet)
            user_records = []
            for i, row in enumerate(all_data, start=1):
                if len(row) > 0 and row[0] == user_id:
                    date = row[1] if len(row) > 1 else ''
                    tip_type = row[2] if len(row) > 2 else ''
                    amount = row[3] if len(row) > 3 else '0'
                    comment = row[4] if len(row) > 4 else ''
                    
                    display_text = f"{date} - {tip_type} - {amount}₽"
                    if comment:
                        display_text += f" - {comment}"
                    
                    user_records.append({
                        'row_index': i,
                        'date': date,
                        'type': tip_type,
                        'amount': amount,
                        'comment': comment,
                        'display_text': display_text
                    })
            return user_records[-10:]  # Последние 10 записей
        
        elif category == "bets":
            sheet = sheets_manager.sheet_bets
            all_data = sheets_manager.get_all_data(sheet)
            user_records = []
            for i, row in enumerate(all_data, start=1):
                if len(row) > 0 and row[0] == user_id:
                    date = row[1] if len(row) > 1 else ''
                    operation = row[2] if len(row) > 2 else ''
                    amount = row[3] if len(row) > 3 else '0'
                    
                    display_text = f"{date} - {operation} - {amount}₽"
                    
                    user_records.append({
                        'row_index': i,
                        'date': date,
                        'operation': operation,
                        'amount': amount,
                        'display_text': display_text
                    })
            return user_records[-10:]  # Последние 10 записей
        
        return []
    
    except Exception as e:
        print(f"Error getting user records: {e}")
        return []

async def show_records_for_deletion(callback: CallbackQuery, records: list, category: str):
    """Показать записи для удаления"""
    keyboard = InlineKeyboardBuilder()
    
    category_names = {
        "income": "доходов",
        "expense": "расходов", 
        "tips": "чаевых",
        "bets": "ставок"
    }
    
    # Добавляем кнопки для каждой записи
    for i, record in enumerate(records):
        # Обрезаем длинный текст для кнопки
        button_text = record['display_text']
        if len(button_text) > 35:
            button_text = button_text[:35] + "..."
        
        keyboard.add(InlineKeyboardButton(
            text=f"❌ {button_text}",
            callback_data=f"select_record_{i}"
        ))
    
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data="delete_back"))
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        f"🗑️ Выбери запись для удаления ({category_names[category]}):\n\n"
        f"📋 Показано последних {len(records)} записей",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith('select_record_'))
async def process_record_selection(callback: CallbackQuery, state: FSMContext):
    record_index = int(callback.data.replace('select_record_', ''))
    
    data = await state.get_data()
    records = data['records']
    category = data['category']
    
    if record_index < len(records):
        selected_record = records[record_index]
        await state.update_data(selected_record=selected_record)
        
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_delete"))
        keyboard.add(InlineKeyboardButton(text="❌ Нет, отмена", callback_data="delete_back"))
        keyboard.adjust(2)
        
        await callback.message.edit_text(
            f"⚠️ Ты уверен что хочешь удалить эту запись?\n\n"
            f"📄 {selected_record['display_text']}",
            reply_markup=keyboard.as_markup()
        )
    
    await callback.answer()

@router.callback_query(lambda c: c.data == 'confirm_delete')
async def confirm_deletion(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_record = data['selected_record']
    category = data['category']
    
    try:
        # Удаляем запись из Google Sheets
        if category == "income":
            sheet = sheets_manager.sheet_income
        elif category == "expense":
            sheet = sheets_manager.sheet_expense
        elif category == "tips":
            sheet = sheets_manager.sheet_tips
        elif category == "bets":
            sheet = sheets_manager.sheet_bets
        else:
            raise ValueError("Unknown category")
        
        # Удаляем строку
        sheet.delete_rows(selected_record['row_index'])
        
        # Сообщение об успешном удалении и сразу в главное меню
        await callback.message.edit_text(
            f"✅ Запись успешно удалена!\n\n"
            f"🗑️ {selected_record['display_text']}\n\n"
            f"🏠 Возврат в главное меню",
            reply_markup=None
        )
        
        # Отправляем главное меню
        await callback.message.answer("Главное меню:", reply_markup=main_kb)
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при удалении записи: {str(e)}\n\n"
            f"🏠 Возврат в главное меню",
            reply_markup=None
        )
        await callback.message.answer("Главное меню:", reply_markup=main_kb)
    
    # Всегда очищаем состояние
    await state.clear()
    await callback.answer()

@router.callback_query(lambda c: c.data == 'delete_back')
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору категории"""
    await delete_records_start(callback.message, state)
    await callback.answer()

@router.callback_query(lambda c: c.data == 'delete_cancel')
async def cancel_deletion(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления - вернуться в главное меню"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Удаление отменено\n\n🏠 Возврат в главное меню",
        reply_markup=None
    )
    await callback.message.answer("Главное меню:", reply_markup=main_kb)
    await callback.answer()

# Обработка кнопки "Назад" из текстового сообщения
@router.message(lambda m: m.text == "⬅️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_kb)
