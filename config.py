# config.py
import os
import json
import logging

logger = logging.getLogger(__name__)

# Все секреты через переменные окружения
TOKEN = os.getenv('BOT_TOKEN')  # ОБЯЗАТЕЛЬНО без значения по умолчанию!
GSHEET_NAME = os.getenv('GSHEET_NAME', 'MyFinance')

# Логируем наличие токена
if not TOKEN:
    logger.error("❌ BOT_TOKEN не установлен!")
else:
    logger.info("✅ BOT_TOKEN найден")

# Google Sheets credentials
GSHEET_CREDS_JSON = os.getenv('GSHEET_CREDS_JSON')
if GSHEET_CREDS_JSON:
    try:
        GSHEET_CREDS = json.loads(GSHEET_CREDS_JSON)
        logger.info("✅ GSHEET_CREDS_JSON загружен")
    except json.JSONDecodeError as e:
        logger.error(f"❌ Ошибка парсинга GSHEET_CREDS_JSON: {e}")
        GSHEET_CREDS = None
else:
    logger.warning("⚠️ GSHEET_CREDS_JSON не установлен")
    # Для локальной разработки
    try:
        with open('creds.json', 'r') as f:
            GSHEET_CREDS = json.load(f)
        logger.info("✅ Локальный creds.json загружен")
    except FileNotFoundError:
        logger.warning("⚠️ Локальный creds.json не найден")
        GSHEET_CREDS = None

# Проверка обязательных переменных
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен! Установите переменную BOT_TOKEN в настройках Railway.")
