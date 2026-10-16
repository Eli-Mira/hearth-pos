"""Menu service for categories, items, and modifiers."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional, List

from app.db.engine import session_scope
from app.db.repositories import CategoryRepository, MenuItemRepository, ModifierRepository
from app.db.models import Category, MenuItem, Modifier
from app.services.auth import auth_service, AuthError
from app.services.money import quantize


class MenuError(Exception):
    pass


class MenuService:
    def get_categories(self) -> List[Category]:
        with session_scope() as session:
            return CategoryRepository(session).get_all_active()
    
    def get_category(self, cat_id: int) -> Optional[Category]:
        with session_scope() as session:
            return CategoryRepository(session).get_by_id(cat_id)
    
    def create_category(self, actor: StaffUser, name: str, sort_order: int = 0, tax_rate_bps: int = 1000) -> Category:
        if not auth_service.check_permission(actor, "menu.manage"):
            raise AuthError("Permission denied")
        with session_scope() as session:
            return CategoryRepository(session).create(name, sort_order, tax_rate_bps)
    
    def update_category(self, actor: StaffUser, cat_id: int, **kwargs) -> bool:
        if not auth_service.check_permission(actor, "menu.manage"):
            raise AuthError("Permission denied")
        with session_scope() as session:
            repo = CategoryRepository(session)
            cat = repo.get_by_id(cat_id)
            if not cat:
                return False
            for key, value in kwargs.items():
                if hasattr(cat, key):
                    setattr(cat, key, value)
            return True
    
    def delete_category(self, actor: StaffUser, cat_id: int) -> bool:
        if not auth_service.check_permission(actor, "menu.manage"):
            raise AuthError("Permission denied")
        with session_scope() as session:
            return CategoryRepository(session).soft_delete(cat_id)
    
    def get_items_by_category(self, category_id: int) -> List[MenuItem]:
        with session_scope() as session:
            return MenuItemRepository(session).get_by_category(category_id)
    
    def get_all_items(self) -> List[MenuItem]:
        with session_scope() as session:
            return MenuItemRepository(session).get_all_active()
    
    def get_item(self, item_id: int) -> Optional[MenuItem]:
        with session_scope() as session:
            return MenuItemRepository(session).get_by_id(item_id)
    
    def create_item(self, actor: StaffUser, category_id: int, name: str, price: Decimal,
                    track_stock: bool = False, stock_qty: int = 0, low_stock_at: int = 5) -> MenuItem:
        if not auth_service.check_permission(actor, "menu.manage"):
            raise AuthError("Permission denied")
        price = quantize(price)
        with session_scope() as session:
            return MenuItemRepository(session).create(
                category_id, name, price, track_stock, stock_qty, low_stock_at
            )
    
    def update_item(self, actor: StaffUser, item_id: int, **kwargs) -> bool:
        if not auth_service.check_permission(actor, "menu.manage"):
            raise AuthError("Permission denied")
        if "price" in kwargs:
            kwargs["price"] = quantize(kwargs["price"])
        with session_scope() as session:
            return MenuItemRepository(session).update(item_id, **kwargs)
    
    def delete_item(self, actor: StaffUser, item_id: int) -> bool:
        if not auth_service.check_permission(actor, "menu.manage"):
            raise AuthError("Permission denied")
        with session_scope() as session:
            return MenuItemRepository(session).soft_delete(item_id)
    
    def get_modifiers(self, menu_item_id: int) -> List[Modifier]:
        with session_scope() as session:
            return ModifierRepository(session).get_by_menu_item(menu_item_id)
    
    def create_modifier(self, actor: StaffUser, menu_item_id: int, name: str, price_delta: Decimal) -> Modifier:
        if not auth_service.check_permission(actor, "menu.manage"):
            raise AuthError("Permission denied")
        price_delta = quantize(price_delta)
        with session_scope() as session:
            return ModifierRepository(session).create(menu_item_id, name, price_delta)
    
    def delete_modifier(self, actor: StaffUser, mod_id: int) -> bool:
        if not auth_service.check_permission(actor, "menu.manage"):
            raise AuthError("Permission denied")
        with session_scope() as session:
            return ModifierRepository(session).soft_delete(mod_id)


menu_service = MenuService()