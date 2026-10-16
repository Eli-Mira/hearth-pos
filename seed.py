"""Idempotent development seed data for Hearth POS."""
from __future__ import annotations

from decimal import Decimal

from app.db.engine import init_db, session_scope
from app.db.models import Category, DiningTable, MenuItem, Modifier, StaffUser, UserRole
from app.services.auth import auth_service


_USERS = (
    ("Manager", "1234", UserRole.MANAGER),
    ("Sarah W.", "2222", UserRole.WAITER),
    ("Mike C.", "3333", UserRole.CASHIER),
    ("Chef Alex", "4444", UserRole.KITCHEN),
)
_CATEGORIES = ("Appetizers", "Mains", "Sides", "Drinks", "Desserts")
_MENU_ITEMS = (
    ("Appetizers", "Wings (6pc)", "12.00"), ("Appetizers", "Calamari", "14.00"),
    ("Appetizers", "Bruschetta", "10.00"), ("Appetizers", "Spinach Dip", "11.00"),
    ("Mains", "Grilled Chicken", "22.00"), ("Mains", "Ribeye Steak", "34.00"),
    ("Mains", "Salmon Fillet", "26.00"), ("Mains", "Pasta Carbonara", "18.00"),
    ("Mains", "Veggie Burger", "16.00"), ("Sides", "Fries", "6.00"),
    ("Sides", "Sweet Potato Fries", "7.00"), ("Sides", "Mashed Potatoes", "5.00"),
    ("Sides", "Grilled Veggies", "6.00"), ("Sides", "Side Salad", "5.00"),
    ("Drinks", "Soft Drink", "3.00"), ("Drinks", "Iced Tea", "3.00"),
    ("Drinks", "Coffee", "3.00"), ("Drinks", "Beer", "7.00"),
    ("Drinks", "Wine Glass", "9.00"), ("Desserts", "Chocolate Cake", "8.00"),
    ("Desserts", "Ice Cream", "6.00"), ("Desserts", "Cheesecake", "9.00"),
)
_MODIFIERS = (
    ("Grilled Chicken", "Extra Sauce", "1.50"), ("Grilled Chicken", "Spicy", "0.00"),
    ("Ribeye Steak", "Peppercorn Sauce", "2.00"), ("Ribeye Steak", "Mushroom Sauce", "2.00"),
    ("Salmon Fillet", "Lemon Butter", "1.00"), ("Salmon Fillet", "Herb Crust", "1.50"),
    ("Fries", "Cheese", "1.00"), ("Fries", "Bacon", "2.00"), ("Fries", "Truffle Oil", "3.00"),
)
_TABLES = ((1, 2), (2, 4), (3, 4), (4, 6), (5, 2), (6, 4), (7, 8), (8, 4), (9, 1), (10, 1))


def create_seed_data() -> None:
    """Fill only missing development records; never overwrite existing POS data."""
    with session_scope() as session:
        users_by_name = {user.name: user for user in session.query(StaffUser).all()}
        for name, pin, role in _USERS:
            if name not in users_by_name:
                session.add(StaffUser(name=name, pin_hash=auth_service.hash_pin(pin), role=role))

        categories_by_name = {category.name: category for category in session.query(Category).all()}
        for position, name in enumerate(_CATEGORIES, start=1):
            if name not in categories_by_name:
                category = Category(name=name, sort_order=position, tax_rate_bps=1000)
                session.add(category)
                categories_by_name[name] = category
        session.flush()

        items_by_name = {item.name: item for item in session.query(MenuItem).all()}
        for category_name, name, price in _MENU_ITEMS:
            if name not in items_by_name:
                item = MenuItem(
                    category_id=categories_by_name[category_name].id,
                    name=name,
                    price=Decimal(price),
                )
                session.add(item)
                items_by_name[name] = item
        session.flush()

        existing_modifiers = {
            (modifier.menu_item_id, modifier.name)
            for modifier in session.query(Modifier).all()
        }
        for item_name, name, price_modifier in _MODIFIERS:
            key = (items_by_name[item_name].id, name)
            if key not in existing_modifiers:
                session.add(Modifier(menu_item_id=key[0], name=name, price_modifier=Decimal(price_modifier)))

        existing_table_numbers = {table.number for table in session.query(DiningTable).all()}
        for number, capacity in _TABLES:
            if number not in existing_table_numbers:
                session.add(DiningTable(number=number, capacity=capacity))


if __name__ == "__main__":
    init_db()
    create_seed_data()
