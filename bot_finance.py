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
from handlers import base_router, income_router, expense_router, reports_router, bets_router

# =======================
# Настройка логирования
# =======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =======================
# Настройка бота
# =======================
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# =======================
# Регистрация роутеров
# =======================
dp.include_router(income_router)
dp.include_router(expense_router)
dp.include_router(reports_router)
dp.include_router(bets_router)
dp.include_router(base_router)

# =======================
# Запуск бота
# =======================
async def main():
    while True:
        try:
            logger.info("🚀 Бот запускается...")
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            logger.info("🔄 Перезапуск через 30 секунд...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
