# utils/user_manager.py
import gspread
from config import GSHEET_CREDS, GSHEET_NAME

# Белый список пользователей
ALLOWED_USERS = [
    "129077607",  # Замени на свой ID
]

class UserSheetsManager:
    def __init__(self):
        if GSHEET_CREDS:
            self.gc = gspread.service_account_from_dict(GSHEET_CREDS)
        else:
            self.gc = gspread.service_account(filename='creds.json')
        
        self.workbook = self.gc.open(GSHEET_NAME)
        
        # Инициализируем листы один раз
        self.sheet_income = self.workbook.worksheet("Доходы")
        self.sheet_expense = self.workbook.worksheet("Расходы") 
        self.sheet_tips = self.workbook.worksheet("Чаевые")
        self.sheet_bets = self.workbook.worksheet("Ставки")
    
    def is_user_allowed(self, user_id: str) -> bool:
        return str(user_id) in ALLOWED_USERS
    
    def get_user_data(self, sheet, user_id: str):
        """Получить данные только для конкретного пользователя"""
        all_data = sheet.get_all_values()
        if not all_data:
            return []
        
        headers = all_data[0]
        user_data = []
        
        for row in all_data[1:]:
            if len(row) > 0 and row[0] == user_id:  # user_id в первом столбце
                user_data.append(row)
        
        return user_data
    
    def append_user_row(self, sheet, user_id: str, values: list):
        """Добавить строку с user_id"""
        row_data = [user_id] + values
        sheet.append_row(row_data)

# Глобальный менеджер
sheets_manager = UserSheetsManager()
