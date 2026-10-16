"""Repository layer for data access."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, List, Sequence

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    StaffUser, UserRole, Category, MenuItem, Modifier, DiningTable, TableStatus,
    Order, OrderType, OrderStatus, OrderItem, Payment, PaymentType,
    Shift, AuditLog, ZReport, SplitSession, SplitSessionStatus, SplitShare, SplitShareStatus,
    Ingredient,
)
from app.config import settings


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: int) -> Optional[StaffUser]:
        return self.session.get(StaffUser, user_id)

    def get_by_name(self, name: str) -> Optional[StaffUser]:
        return self.session.execute(
            select(StaffUser).where(StaffUser.name == name, StaffUser.is_deleted == False)
        ).scalar_one_or_none()

    def get_active_by_role(self, role: UserRole) -> List[StaffUser]:
        return list(self.session.execute(
            select(StaffUser).where(StaffUser.role == role, StaffUser.active == True, StaffUser.is_deleted == False)
        ).scalars().all())

    def get_all_active(self) -> List[StaffUser]:
        return list(self.session.execute(
            select(StaffUser).where(StaffUser.active == True, StaffUser.is_deleted == False)
        ).scalars().all())

    def create(self, name: str, pin_hash: str, role: UserRole) -> StaffUser:
        user = StaffUser(name=name, pin_hash=pin_hash, role=role)
        self.session.add(user)
        self.session.flush()
        return user

    def update_pin(self, user_id: int, pin_hash: str) -> bool:
        user = self.get_by_id(user_id)
        if user:
            user.pin_hash = pin_hash
            return True
        return False

    def soft_delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if user:
            user.is_deleted = True
            user.active = False
            return True
        return False


class CategoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all_active(self) -> List[Category]:
        return list(self.session.execute(
            select(Category).where(Category.is_deleted == False).order_by(Category.sort_order)
        ).scalars().all())

    def get_by_id(self, cat_id: int) -> Optional[Category]:
        return self.session.get(Category, cat_id)

    def create(self, name: str, sort_order: int = 0, tax_rate_bps: int = 1000) -> Category:
        cat = Category(name=name, sort_order=sort_order, tax_rate_bps=tax_rate_bps)
        self.session.add(cat)
        self.session.flush()
        return cat

    def soft_delete(self, cat_id: int) -> bool:
        cat = self.get_by_id(cat_id)
        if cat:
            cat.is_deleted = True
            return True
        return False


class MenuItemRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, item_id: int) -> Optional[MenuItem]:
        return self.session.execute(
            select(MenuItem).options(selectinload(MenuItem.modifiers)).where(MenuItem.id == item_id)
        ).scalar_one_or_none()

    def get_by_category(self, category_id: int) -> List[MenuItem]:
        return list(self.session.execute(
            select(MenuItem).options(selectinload(MenuItem.modifiers)).where(
                MenuItem.category_id == category_id, MenuItem.is_deleted == False
            ).order_by(MenuItem.name)
        ).scalars().all())

    def get_all_active(self) -> List[MenuItem]:
        return list(self.session.execute(
            select(MenuItem).options(selectinload(MenuItem.modifiers)).where(MenuItem.is_deleted == False)
        ).scalars().all())

    def create(self, category_id: int, name: str, price: Decimal, track_stock: bool = False,
               stock_qty: int = 0, low_stock_at: int = 5) -> MenuItem:
        item = MenuItem(
            category_id=category_id, name=name, price=price,
            track_stock=track_stock, stock_qty=stock_qty, low_stock_at=low_stock_at
        )
        self.session.add(item)
        self.session.flush()
        return item

    def update(self, item_id: int, **kwargs) -> bool:
        item = self.get_by_id(item_id)
        if item:
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            return True
        return False

    def soft_delete(self, item_id: int) -> bool:
        item = self.get_by_id(item_id)
        if item:
            item.is_deleted = True
            return True
        return False


class ModifierRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_menu_item(self, menu_item_id: int) -> List[Modifier]:
        return list(self.session.execute(
            select(Modifier).where(Modifier.menu_item_id == menu_item_id, Modifier.is_deleted == False)
        ).scalars().all())

    def create(self, menu_item_id: int, name: str, price_modifier: Decimal) -> Modifier:
            mod = Modifier(menu_item_id=menu_item_id, name=name, price_modifier=price_modifier)
            self.session.add(mod)
            self.session.flush()
            return mod

    def soft_delete(self, mod_id: int) -> bool:
        mod = self.session.get(Modifier, mod_id)
        if mod:
            mod.is_deleted = True
            return True
        return False


class TableRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, table_id: int) -> Optional[DiningTable]:
        return self.session.get(DiningTable, table_id)

    def get_by_number(self, number: int) -> Optional[DiningTable]:
        return self.session.execute(
            select(DiningTable).where(DiningTable.number == number, DiningTable.is_deleted == False)
        ).scalar_one_or_none()

    def get_all_active(self) -> List[DiningTable]:
        return list(self.session.execute(
            select(DiningTable).where(DiningTable.is_deleted == False).order_by(DiningTable.number)
        ).scalars().all())

    def get_by_status(self, status: TableStatus) -> List[DiningTable]:
        return list(self.session.execute(
            select(DiningTable).where(DiningTable.status == status, DiningTable.is_deleted == False)
        ).scalars().all())

    def create(self, number: int, capacity: int = 4) -> DiningTable:
            table = DiningTable(number=number, capacity=capacity)
            self.session.add(table)
            self.session.flush()
            return table

    def update_status(self, table_id: int, status: TableStatus) -> bool:
        table = self.get_by_id(table_id)
        if table:
            table.status = status
            return True
        return False


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self.session.execute(
            select(Order).options(
                selectinload(Order.items).selectinload(OrderItem.modifiers),
                selectinload(Order.payments),
                selectinload(Order.table)
            ).where(Order.id == order_id)
        ).scalar_one_or_none()

    def get_active_for_table(self, table_id: int) -> Optional[Order]:
        return self.session.execute(
            select(Order).where(
                Order.table_id == table_id,
                Order.status.in_([OrderStatus.OPEN, OrderStatus.SENT_TO_KITCHEN, OrderStatus.IN_PROGRESS, OrderStatus.READY, OrderStatus.BILL_REQUESTED]),
                Order.is_deleted == False
            )
        ).scalar_one_or_none()

    def get_active_takeaway(self) -> List[Order]:
        return list(self.session.execute(
            select(Order).where(
                Order.order_type == OrderType.TAKEAWAY,
                Order.status.in_([OrderStatus.OPEN, OrderStatus.SENT_TO_KITCHEN, OrderStatus.IN_PROGRESS, OrderStatus.READY, OrderStatus.BILL_REQUESTED]),
                Order.is_deleted == False
            ).order_by(Order.opened_at)
        ).scalars().all())

    def create(self, order_type: OrderType, opened_by: int, table_id: Optional[int] = None) -> Order:
            order = Order(order_type=order_type, actor_id=opened_by, table_id=table_id)
            self.session.add(order)
            self.session.flush()
            return order

    def update_totals(self, order_id: int, subtotal: Decimal, tax_total: Decimal, total: Decimal) -> bool:
        order = self.get_by_id(order_id)
        if order:
            order.subtotal = subtotal
            order.tax_total = tax_total
            order.total = total
            return True
        return False

    def update_status(self, order_id: int, status: OrderStatus) -> bool:
        order = self.get_by_id(order_id)
        if order:
            order.status = status
            if status in (OrderStatus.PAID, OrderStatus.CLOSED):
                order.closed_at = datetime.now(timezone.utc)
            return True
        return False

    def get_recent(self, limit: int = 50) -> List[Order]:
        return list(self.session.execute(
            select(Order).where(Order.is_deleted == False).order_by(Order.opened_at.desc()).limit(limit)
        ).scalars().all())


class OrderItemRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_item(self, order_id: int, menu_item: MenuItem, qty: int = 1,
                 modifiers: Optional[List[Modifier]] = None) -> OrderItem:
        """Persist a snapshot line item using the current OrderItem schema."""
        if qty < 1:
            raise ValueError("qty must be at least one")
        if menu_item.category is None:
            raise ValueError("menu item must have a category")

        selected_modifiers = modifiers or []
        modifier_total = sum((modifier.price_modifier for modifier in selected_modifiers), Decimal("0.00"))
        unit_price = menu_item.price + modifier_total
        tax_rate = Decimal(menu_item.category.tax_rate_bps) / Decimal("10000")
        unit_base = (unit_price / (Decimal("1") + tax_rate)).quantize(Decimal("0.01"))
        unit_tax = (unit_price - unit_base).quantize(Decimal("0.01"))

        item = OrderItem(
            order_id=order_id,
            menu_item_id=menu_item.id,
            category_id=menu_item.category_id,
            name_snapshot=menu_item.name,
            quantity=qty,
            unit_price=unit_price,
            total_price=(unit_price * qty).quantize(Decimal("0.01")),
            unit_base=unit_base,
            unit_tax=unit_tax,
            tax_rate_bps=menu_item.category.tax_rate_bps,
        )
        item.modifiers.extend(selected_modifiers)
        self.session.add(item)
        self.session.flush()
        return item

    def update_qty(self, item_id: int, qty: int) -> bool:
        if qty < 1:
            return False
        item = self.session.get(OrderItem, item_id)
        if item and not item.voided:
            item.quantity = qty
            item.total_price = (item.unit_price * qty).quantize(Decimal("0.01"))
            return True
        return False

    def void_item(self, item_id: int, reason: str, approved_by: Optional[int] = None) -> bool:
        item = self.session.get(OrderItem, item_id)
        if item and not item.voided:
            item.voided = True
            item.void_reason = reason
            item.void_approved_by = approved_by
            return True
        return False

    def get_by_id(self, item_id: int) -> Optional[OrderItem]:
        return self.session.execute(
            select(OrderItem).options(selectinload(OrderItem.modifiers)).where(OrderItem.id == item_id)
        ).scalar_one_or_none()


class PaymentRepository:
    def __init__(self, session: Session):
        self.session = session

    def add_payment(self, order_id: int, payment_type: PaymentType, amount: Decimal,
                    tendered: Decimal, change: Decimal, created_by: int) -> Payment:
        payment = Payment(
            order_id=order_id,
            created_by=created_by,
            payment_type=payment_type,
            amount=amount,
            tendered=tendered,
            change=change,
        )
        self.session.add(payment)
        self.session.flush()
        return payment

    def get_for_order(self, order_id: int) -> List[Payment]:
        return list(self.session.execute(
            select(Payment).where(Payment.order_id == order_id)
        ).scalars().all())

    def get_total_paid(self, order_id: int) -> Decimal:
        result = self.session.execute(
            select(func.coalesce(func.sum(Payment.amount), Decimal("0.00")))
            .where(Payment.order_id == order_id)
        ).scalar()
        return result or Decimal("0.00")


class ShiftRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_current_shift(self) -> Optional[Shift]:
        """Alias for get_current_open for backward compatibility."""
        return self.get_current_open()

    def get_current_open(self) -> Optional[Shift]:
        return self.session.execute(
            select(Shift).where(Shift.closed_at.is_(None)).order_by(Shift.opened_at.desc())
        ).scalar_one_or_none()

    def open_shift(self, opened_by: int, opening_float: Decimal) -> Shift:
        shift = Shift(opened_by=opened_by, opening_float=opening_float)
        self.session.add(shift)
        self.session.flush()
        return shift

    def close_shift(self, shift_id: int, closing_counted: Decimal, signoff_by: Optional[int] = None) -> Optional[Shift]:
        shift = self.session.get(Shift, shift_id)
        if shift and shift.closed_at is None:
            shift.closed_at = datetime.now(timezone.utc)
            shift.closing_counted = closing_counted
            shift.signoff_by = signoff_by
            return shift
        return None

    def update_expected(self, shift_id: int, expected: Decimal) -> bool:
        shift = self.session.get(Shift, shift_id)
        if shift:
            shift.closing_expected = expected
            return True
        return False

    def get_by_id(self, shift_id: int) -> Optional[Shift]:
        return self.session.get(Shift, shift_id)


class AuditRepository:
    def __init__(self, session: Session):
        self.session = session

    def log(self, actor_id: int, action: str, entity: str, entity_id: int, payload: dict) -> AuditLog:
        import json
        log = AuditLog(
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            payload_json=json.dumps(payload, default=str)
        )
        self.session.add(log)
        self.session.flush()
        return log


class SplitSessionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, session_id: int) -> Optional[SplitSession]:
        return self.session.execute(
            select(SplitSession).options(selectinload(SplitSession.shares)).where(SplitSession.id == session_id)
        ).scalar_one_or_none()

    def get_by_id_with_order(self, session_id: int) -> Optional[SplitSession]:
        return self.session.execute(
            select(SplitSession).options(
                selectinload(SplitSession.shares),
                selectinload(SplitSession.order)
            ).where(SplitSession.id == session_id)
        ).scalar_one_or_none()

    def get_active_for_order(self, order_id: int) -> Optional[SplitSession]:
        return self.session.execute(
            select(SplitSession).where(
                SplitSession.order_id == order_id,
                SplitSession.status == SplitSessionStatus.ACTIVE
            )
        ).scalar_one_or_none()

    def get_by_order(self, order_id: int) -> List[SplitSession]:
        return list(self.session.execute(
            select(SplitSession).where(SplitSession.order_id == order_id).order_by(SplitSession.created_at.desc())
        ).scalars().all())

    def create(self, order_id: int, total_ways: int, total_amount: Decimal) -> SplitSession:
        split_session = SplitSession(
            order_id=order_id,
            total_ways=total_ways,
            total_amount=total_amount,
            status=SplitSessionStatus.ACTIVE,
        )
        self.session.add(split_session)
        self.session.flush()
        return split_session

    def update_status(self, session_id: int, status: SplitSessionStatus, completed_at: Optional[datetime] = None) -> bool:
        split_session = self.get_by_id(session_id)
        if split_session:
            split_session.status = status
            if status == SplitSessionStatus.COMPLETED:
                split_session.completed_at = completed_at or datetime.now(timezone.utc)
            return True
        return False

    def get_active_sessions(self) -> List[SplitSession]:
        return list(self.session.execute(
            select(SplitSession).where(SplitSession.status == SplitSessionStatus.ACTIVE).order_by(SplitSession.created_at)
        ).scalars().all())

    def get_abandoned_candidates(self, cutoff_minutes: int = 15) -> List[SplitSession]:
        """Get active sessions that have been active longer than cutoff_minutes."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=cutoff_minutes)
        return list(self.session.execute(
            select(SplitSession).where(
                SplitSession.status == SplitSessionStatus.ACTIVE,
                SplitSession.created_at < cutoff
            )
        ).scalars().all())


class SplitShareRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, share_id: int) -> Optional[SplitShare]:
        return self.session.get(SplitShare, share_id)

    def get_by_session(self, session_id: int) -> List[SplitShare]:
        return list(self.session.execute(
            select(SplitShare).where(SplitShare.split_session_id == session_id).order_by(SplitShare.share_index)
        ).scalars().all())

    def get_unpaid_for_session(self, session_id: int) -> List[SplitShare]:
        return list(self.session.execute(
            select(SplitShare).where(
                SplitShare.split_session_id == session_id,
                SplitShare.status == SplitShareStatus.UNPAID
            ).order_by(SplitShare.share_index)
        ).scalars().all())

    def get_paid_for_session(self, session_id: int) -> List[SplitShare]:
        return list(self.session.execute(
            select(SplitShare).where(
                SplitShare.split_session_id == session_id,
                SplitShare.status == SplitShareStatus.PAID
            ).order_by(SplitShare.share_index)
        ).scalars().all())

    def get_by_status(self, session_id: int, status: SplitShareStatus) -> List[SplitShare]:
        return list(self.session.execute(
            select(SplitShare).where(
                SplitShare.split_session_id == session_id,
                SplitShare.status == status
            ).order_by(SplitShare.share_index)
        ).scalars().all())

    def create(self, split_session_id: int, share_index: int, amount: Decimal) -> SplitShare:
        share = SplitShare(
            split_session_id=split_session_id,
            share_index=share_index,
            amount=amount,
            status=SplitShareStatus.UNPAID,
        )
        self.session.add(share)
        self.session.flush()
        return share

    def create_shares(self, split_session_id: int, amounts: List[Decimal]) -> List[SplitShare]:
        shares = []
        for i, amount in enumerate(amounts):
            share = SplitShare(
                split_session_id=split_session_id,
                share_index=i,
                amount=amount,
                status=SplitShareStatus.UNPAID,
            )
            self.session.add(share)
            shares.append(share)
        self.session.flush()
        return shares

    def mark_paid(self, share_id: int, payment_id: int) -> bool:
        share = self.get_by_id(share_id)
        if share and share.status == SplitShareStatus.UNPAID:
            share.status = SplitShareStatus.PAID
            share.payment_id = payment_id
            share.paid_at = datetime.now(timezone.utc)
            return True
        return False

    def mark_void(self, share_id: int) -> bool:
        share = self.get_by_id(share_id)
        if share and share.status == SplitShareStatus.UNPAID:
            share.status = SplitShareStatus.VOID
            return True
        return False

    def get_unpaid_count(self, session_id: int) -> int:
        result = self.session.execute(
            select(func.count(SplitShare.id)).where(
                SplitShare.split_session_id == session_id,
                SplitShare.status == SplitShareStatus.UNPAID
            )
        ).scalar()
        return result or 0

    def get_paid_count(self, session_id: int) -> int:
        result = self.session.execute(
            select(func.count(SplitShare.id)).where(
                SplitShare.split_session_id == session_id,
                SplitShare.status == SplitShareStatus.PAID
            )
        ).scalar()
        return result or 0

    def get_total_paid_amount(self, session_id: int) -> Decimal:
        result = self.session.execute(
            select(func.coalesce(func.sum(SplitShare.amount), Decimal("0.00"))).where(
                SplitShare.split_session_id == session_id,
                SplitShare.status == SplitShareStatus.PAID
            )
        ).scalar()
        return result or Decimal("0.00")


class ZReportRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, shift_id: int, snapshot: dict) -> ZReport:
        import json
        report = ZReport(shift_id=shift_id, json_snapshot=json.dumps(snapshot, default=str))
        self.session.add(report)
        self.session.flush()
        return report

    def get_for_shift(self, shift_id: int) -> Optional[ZReport]:
        return self.session.execute(
            select(ZReport).where(ZReport.shift_id == shift_id)
        ).scalar_one_or_none()


class IngredientRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_low_stock_ingredients(self):
        """Return list of ingredients where quantity < low_stock_threshold."""
        return self.session.query(Ingredient).filter(Ingredient.quantity < Ingredient.low_stock_threshold).all()
