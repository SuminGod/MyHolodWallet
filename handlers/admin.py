# handlers/admin.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from utils.user_manager import ALLOWED_USERS

router = Router()

class AdminStates(StatesGroup):
    waiting_user_id = State()

# ID администратора (замени на свой)
ADMIN_ID = "129077607"  # Замени на свой Telegram ID

def is_admin(user_id: str) -> bool:
    return str(user_id) == ADMIN_ID

@router.message(Command("admin"))
async def admin_panel(message: Message):
    user_id = str(message.from_user.id)
    
    if not is_admin(user_id):
        await message.answer("❌ Недостаточно прав")
        return
    
    users_list = "\n".join([f"👤 {user_id}" for user_id in ALLOWED_USERS])
    
    await message.answer(
        f"🛠️ Панель администратора\n\n"
        f"Доступные пользователи ({len(ALLOWED_USERS)}):\n{users_list}\n\n"
        f"Команды:\n"
        f"/add_user - добавить пользователя\n"
        f"/remove_user - удалить пользователя"
    )

@router.message(Command("add_user"))
async def add_user_start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    
    if not is_admin(user_id):
        await message.answer("❌ Недостаточно прав")
        return
    
    await state.set_state(AdminStates.waiting_user_id)
    await message.answer("Введите ID пользователя для добавления:")

@router.message(AdminStates.waiting_user_id)
async def add_user_complete(message: Message, state: FSMContext):
    new_user_id = message.text.strip()
    
    try:
        # Проверяем что ID состоит из цифр
        int(new_user_id)
        
        if new_user_id in ALLOWED_USERS:
            await message.answer("❌ Этот пользователь уже есть в списке")
        else:
            ALLOWED_USERS.append(new_user_id)
            await message.answer(f"✅ Пользователь {new_user_id} добавлен в белый список")
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. ID должен состоять только из цифр.")

@router.message(Command("remove_user"))
async def remove_user_start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    
    if not is_admin(user_id):
        await message.answer("❌ Недостаточно прав")
        return
    
    users_list = "\n".join([f"{i+1}. {user_id}" for i, user_id in enumerate(ALLOWED_USERS) if user_id != ADMIN_ID])
    
    if users_list:
        await message.answer(
            f"Выберите пользователя для удаления:\n\n{users_list}\n\n"
            f"Отправьте номер пользователя из списка:"
        )
        await state.set_state(AdminStates.waiting_user_id)
    else:
        await message.answer("❌ Нет пользователей для удаления")

# Добавь этот обработчик в __init__.py
