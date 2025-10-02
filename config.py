# config.py
import os
import json

# Все секреты через переменные окружения
TOKEN = os.getenv('BOT_TOKEN')  # ОБЯЗАТЕЛЬНО без значения по умолчанию!
GSHEET_NAME = os.getenv('GSHEET_NAME', 'MyFinance')

# Google Sheets credentials
GSHEET_CREDS_JSON = os.getenv('GSHEET_CREDS_JSON')
if GSHEET_CREDS_JSON:
    GSHEET_CREDS = json.loads(GSHEET_CREDS_JSON)
else:
    # Для локальной разработки
    try:
        with open('creds.json', 'r') as f:
            GSHEET_CREDS = json.load(f)
    except FileNotFoundError:
        GSHEET_CREDS = None

# Проверка обязательных переменных
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен!")