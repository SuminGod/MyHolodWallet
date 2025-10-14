# handlers/__init__.py
from .base import router as base_router
from .income import router as income_router
from .expense import router as expense_router
from .reports import router as reports_router
from .bets import router as bets_router
from .firm_payment import router as firm_payment_router
from .admin import router as admin_router
from .delete_records import router as delete_router

__all__ = [
    'base_router', 
    'income_router', 
    'expense_router', 
    'reports_router', 
    'bets_router', 
    'firm_payment_router',
    'admin_router',
    'delete_router'
]
