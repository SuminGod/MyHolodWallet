# bot_finance.py
import logging
import asyncio
import sys
import os

# Добавляем путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN
from handlers import base_router, income_router, expense_router, reports_router, bets_router, firm_payment_router, admin_router, delete_router
# =======================
# Настройка логирования
# =======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # =======================
    # Настройка бота
    # =======================
    try:
        logger.info("🚀 Инициализация бота...")
        bot = Bot(token=TOKEN)
        dp = Dispatcher(storage=MemoryStorage())
        
        # =======================
        # Регистрация роутеров
        # =======================
        dp.include_router(admin_router) 
        dp.include_router(income_router)
        dp.include_router(expense_router)
        dp.include_router(reports_router)
        dp.include_router(bets_router)
        dp.include_router(firm_payment_router)  # ДОБАВЬ ЭТУ СТРОЧКУ
        dp.include_router(base_router)
        dp.include_router(delete_router) 
        
        logger.info("✅ Все роутеры зарегистрированы")
        logger.info("🤖 Бот готов к работе")
        
        # =======================
        # Запуск бота
        # =======================
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при инициализации: {e}")
        logger.info("🔄 Перезапуск через 30 секунд...")
        await asyncio.sleep(30)
        await main()

if __name__ == "__main__":
    asyncio.run(main())


