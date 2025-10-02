# bot_finance.py
import logging
import asyncio
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
# Регистрация роутеров - ВАЖНО: base_router ПОСЛЕДНИМ!
# =======================
dp.include_router(income_router)
dp.include_router(expense_router) 
dp.include_router(reports_router)
dp.include_router(bets_router)
dp.include_router(base_router)  # base_router ДОЛЖЕН БЫТЬ ПОСЛЕДНИМ!


# После регистрации роутеров добавь:
print("✅ Порядок роутеров:")
for i, router in enumerate(dp.sub_routers):
    print(f"   {i+1}. {router}")
    
# =======================
# Запуск бота
# =======================
async def main():
    try:
        logger.info("🚀 Бот запускается...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())