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
    confirm_delete = State()

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
            "❌ В этой категории нет записей для удаления",
            reply_markup=InlineKeyboardBuilder()
                .add(InlineKeyboardButton(text="⬅️ Назад", callback_data="delete_back"))
                .as_markup()
        )
        return
    
    await state.update_data(records=records)
    await show_records_for_deletion(callback.message, records, category, state)
    await callback.answer()

async def get_user_records(user_id: str, category: str):
    """Получить записи пользователя для указанной категории"""
    try:
        if category == "income":
            sheet = sheets_manager.sheet_income
            all_data = sheets_manager.get_all_data(sheet)
            user_records = []
            for i, row in enumerate(all_data, start=1):
                if len(row) > 0 and row[0] == user_id:
                    user_records.append({
                        'row_index': i,
                        'date': row[1] if len(row) > 1 else '',
                        'source': row[2] if len(row) > 2 else '',
                        'request_number': row[3] if len(row) > 3 else '',
                        'amount': row[4] if len(row) > 4 else '',
                        'display_text': f"{row[1]} - {row[2]} - {row[4]} ₽" if len(row) > 4 else 'Неполные данные'
                    })
            return user_records[-10:]  # Последние 10 записей
        
        elif category == "expense":
            sheet = sheets_manager.sheet_expense
            all_data = sheets_manager.get_all_data(sheet)
            user_records = []
            for i, row in enumerate(all_data, start=1):
                if len(row) > 0 and row[0] == user_id:
                    user_records.append({
                        'row_index': i,
                        'date': row[1] if len(row) > 1 else '',
                        'category': row[2] if len(row) > 2 else '',
                        'amount': row[3] if len(row) > 3 else '',
                        'display_text': f"{row[1]} - {row[2]} - {row[3]} ₽" if len(row) > 3 else 'Неполные данные'
                    })
            return user_records[-10:]  # Последние 10 записей
        
        elif category == "tips":
            sheet = sheets_manager.sheet_tips
            all_data = sheets_manager.get_all_data(sheet)
            user_records = []
            for i, row in enumerate(all_data, start=1):
                if len(row) > 0 and row[0] == user_id:
                    user_records.append({
                        'row_index': i,
                        'date': row[1] if len(row) > 1 else '',
                        'type': row[2] if len(row) > 2 else '',
                        'amount': row[3] if len(row) > 3 else '',
                        'display_text': f"{row[1]} - {row[2]} - {row[3]} ₽" if len(row) > 3 else 'Неполные данные'
                    })
            return user_records[-10:]  # Последние 10 записей
        
        elif category == "bets":
            sheet = sheets_manager.sheet_bets
            all_data = sheets_manager.get_all_data(sheet)
            user_records = []
            for i, row in enumerate(all_data, start=1):
                if len(row) > 0 and row[0] == user_id:
                    user_records.append({
                        'row_index': i,
                        'date': row[1] if len(row) > 1 else '',
                        'operation': row[2] if len(row) > 2 else '',
                        'amount': row[3] if len(row) > 3 else '',
                        'display_text': f"{row[1]} - {row[2]} - {row[3]} ₽" if len(row) > 3 else 'Неполные данные'
                    })
            return user_records[-10:]  # Последние 10 записей
        
        return []
    
    except Exception as e:
        print(f"Error getting user records: {e}")
        return []

async def show_records_for_deletion(message: Message, records: list, category: str, state: FSMContext):
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
        keyboard.add(InlineKeyboardButton(
            text=f"❌ {record['display_text']}",
            callback_data=f"select_record_{i}"
        ))
    
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="delete_back"))
    keyboard.adjust(1)
    
    await message.edit_text(
        f"🗑️ Выбери запись для удаления ({category_names[category]}):\n\n"
        f"📋 Показано последних {len(records)} записей",
        reply_markup=keyboard.as_markup()
    )

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
        
        await callback.message.edit_text(
            f"✅ Запись успешно удалена!\n"
            f"🗑️ {selected_record['display_text']}",
            reply_markup=InlineKeyboardBuilder()
                .add(InlineKeyboardButton(text="🗑️ Удалить ещё", callback_data="delete_more"))
                .add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="delete_main"))
                .adjust(2)
                .as_markup()
        )
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при удалении записи: {str(e)}",
            reply_markup=InlineKeyboardBuilder()
                .add(InlineKeyboardButton(text="⬅️ Назад", callback_data="delete_back"))
                .as_markup()
        )
    
    await callback.answer()

@router.callback_query(lambda c: c.data == 'delete_more')
async def delete_more_records(callback: CallbackQuery, state: FSMContext):
    await delete_records_start(callback.message, state)
    await callback.answer()

@router.callback_query(lambda c: c.data in ['delete_back', 'delete_cancel'])
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    await delete_records_start(callback.message, state)
    await callback.answer()

@router.callback_query(lambda c: c.data == 'delete_main')
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏠 Возврат в главное меню",
        reply_markup=None
    )
    await callback.message.answer("Главное меню:", reply_markup=main_kb)
    await callback.answer()

# Обработка кнопки "Назад"
@router.message(lambda m: m.text == "⬅️ Назад")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_kb)
