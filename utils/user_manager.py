# utils/user_manager.py
import gspread
from config import GSHEET_CREDS, GSHEET_NAME

# Белый список пользователей
ALLOWED_USERS = [
    "129077607",  # Замени на свой реальный Telegram ID
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
        self.sheet_debts = self.workbook.worksheet("Долги")
    
    def is_user_allowed(self, user_id: str) -> bool:
        return str(user_id) in ALLOWED_USERS
    
    def get_user_data(self, sheet, user_id: str):
        """Получить данные только для конкретного пользователя"""
        try:
            all_data = sheet.get_all_values()
            if not all_data:
                return []
            
            user_data = []
            
            for row in all_data:
                if len(row) > 0 and row[0] == user_id:  # user_id в первом столбце
                    user_data.append(row)
            
            return user_data
        except Exception as e:
            print(f"Error getting user data: {e}")
            return []
    
    def get_all_data(self, sheet):
        """Получить все данные из листа"""
        try:
            return sheet.get_all_values()
        except Exception as e:
            print(f"Error getting all data: {e}")
            return []
    
    def append_user_row(self, sheet, user_id: str, values: list):
        """Добавить строку с user_id"""
        try:
            row_data = [user_id] + values
            sheet.append_row(row_data)
            return True
        except Exception as e:
            print(f"Error appending row: {e}")
            return False

# Глобальный менеджер
sheets_manager = UserSheetsManager()
