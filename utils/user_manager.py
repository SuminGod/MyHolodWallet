import gspread
from config import GSHEET_CREDS, GSHEET_NAME

# Белый список пользователей (добавь сюда ID своих пользователей)
ALLOWED_USERS = [
    "129077607",           # Замени на свой Telegram ID
    "USER_ID_ДРУГА",          # Замени на ID друга
    # Можно добавить других пользователей
]

class UserSheetsManager:
    def __init__(self):
        if GSHEET_CREDS:
            self.gc = gspread.service_account_from_dict(GSHEET_CREDS)
        else:
            self.gc = gspread.service_account(filename='creds.json')
        
        self.workbook = self.gc.open(GSHEET_NAME)
    
    def is_user_allowed(self, user_id: str) -> bool:
        """Проверить, есть ли пользователь в белом списке"""
        return str(user_id) in ALLOWED_USERS
    
    def get_sheet(self, user_id: str, sheet_type: str):
        """Получить лист для конкретного пользователя"""
        if not self.is_user_allowed(user_id):
            raise PermissionError("Пользователь не имеет доступа к боту")
        
        sheet_name = f"user_{user_id}_{sheet_type}"
        try:
            return self.workbook.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            # Создаем новый лист с заголовками
            worksheet = self.workbook.add_worksheet(sheet_name, 1000, 20)
            
            # Устанавливаем заголовки в зависимости от типа
            if sheet_type == "income":
                worksheet.append_row(["Дата", "Источник", "№ заявки", "Сумма чека", "Мой доход", "Долг фирме", "Статус оплаты"])
            elif sheet_type == "expense":
                worksheet.append_row(["Дата", "Категория", "Сумма", "Комментарий"])
            elif sheet_type == "tips":
                worksheet.append_row(["Дата", "Тип", "Сумма", "Комментарий"])
            elif sheet_type == "bets":
                worksheet.append_row(["Дата", "Операция", "Сумма"])
            
            return worksheet

# Глобальный менеджер
sheets_manager = UserSheetsManager()
