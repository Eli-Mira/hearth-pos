"""SQLAlchemy models for the POS system."""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, 
    Enum, Numeric, Index, Table
)
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column

Base = declarative_base()

# Association table: order_items <-> modifiers (many-to-many)
order_items_modifiers = Table(
    'order_item_modifiers', Base.metadata,
    Column('order_item_id', Integer, ForeignKey('order_items.id'), primary_key=True),
    Column('modifier_id', Integer, ForeignKey('modifiers.id'), primary_key=True),
)

def _utcnow() -> datetime:
    """Current UTC time as a tz-aware datetime."""
    return datetime.now(timezone.utc)


# --- Enums ---

class UserRole(str, enum.Enum):
    CASHIER = "cashier"
    WAITER = "waiter"
    KITCHEN = "kitchen"
    MANAGER = "manager"

class OrderStatus(str, enum.Enum):
    OPEN = "open"
    HELD = "held"
    SENT_TO_KITCHEN = "sent_to_kitchen"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    BILL_REQUESTED = "bill_requested"
    PAID = "paid"
    CLOSED = "closed"
    VOIDED = "voided"

class OrderType(str, enum.Enum):
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    DELIVERY = "delivery"

class PaymentType(str, enum.Enum):
    CASH = "cash"
    CARD_MANUAL = "card_manual"

class TableStatus(str, enum.Enum):
    OPEN = "open"
    SEATED = "seated"
    ORDERED = "ordered"
    BILL_REQUESTED = "bill_requested"
    DIRTY = "dirty"

class SplitSessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class SplitShareStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    VOID = "void"


# --- Staff & Users ---

class StaffUser(Base):
    __tablename__ = "staff_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    orders_opened: Mapped[List["Order"]] = relationship("Order", back_populates="opened_by_user")
    payments_created: Mapped[List["Payment"]] = relationship("Payment", back_populates="created_by_user")
    shifts_opened: Mapped[List["Shift"]] = relationship("Shift", foreign_keys="Shift.opened_by", back_populates="opened_by_user")
    shifts_signed_off: Mapped[List["Shift"]] = relationship("Shift", foreign_keys="Shift.signoff_by", back_populates="signoff_by_user")


# --- Menu ---

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tax_rate_bps: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    items: Mapped[List["MenuItem"]] = relationship("MenuItem", back_populates="category")
    __table_args__ = (Index("ix_categories_sort_order", "sort_order"),)


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    track_stock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stock_qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_stock_at: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="items")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="menu_item")
    modifiers: Mapped[List["Modifier"]] = relationship("Modifier", back_populates="menu_item")


class Modifier(Base):
    __tablename__ = "modifiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    menu_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("menu_items.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    price_modifier: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="modifiers")

    @property
    def name_snapshot(self) -> str:
        """Legacy receipt alias for the modifier label."""
        return self.name

    @property
    def price_delta(self) -> Decimal:
        """Legacy receipt alias for the modifier amount."""
        return self.price_modifier

# --- Orders ---

class DiningTable(Base):
    __tablename__ = "dining_tables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    capacity: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    status: Mapped[TableStatus] = mapped_column(Enum(TableStatus), nullable=False, default=TableStatus.OPEN)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    orders: Mapped[List["Order"]] = relationship("Order", back_populates="table")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[int] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=False)
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType), nullable=False)
    table_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("dining_tables.id"), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False, default=OrderStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    opened_by_user: Mapped["StaffUser"] = relationship("StaffUser", back_populates="orders_opened")
    table: Mapped[Optional["DiningTable"]] = relationship("DiningTable", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="order")

    @property
    def opened_by(self) -> int:
        """Legacy alias for the staff member who opened the order."""
        return self.actor_id


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("menu_items.id"), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_base: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    unit_tax: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    tax_rate_bps: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    voided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    void_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    void_approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="order_items")
    category: Mapped[Optional["Category"]] = relationship("Category")
    modifiers: Mapped[List["Modifier"]] = relationship("Modifier", secondary=order_items_modifiers)


    @property
    def qty(self) -> int:
        """Legacy alias for quantity."""
        return self.quantity

    @qty.setter
    def qty(self, value: int) -> None:
        self.quantity = value


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tendered: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    change: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    payment_type: Mapped[PaymentType] = mapped_column(Enum(PaymentType), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="payments")
    created_by_user: Mapped["StaffUser"] = relationship("StaffUser", back_populates="payments_created")


# --- Audit & Reporting ---

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[int] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    opened_by: Mapped[int] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    opening_float: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    closing_counted: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    closing_expected: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    variance: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    signoff_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("staff_users.id"), nullable=True)

    opened_by_user: Mapped["StaffUser"] = relationship("StaffUser", foreign_keys="[Shift.opened_by]", back_populates="shifts_opened")
    signoff_by_user: Mapped[Optional["StaffUser"]] = relationship("StaffUser", foreign_keys="[Shift.signoff_by]", back_populates="shifts_signed_off")


class ZReport(Base):
    __tablename__ = "z_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shift_id: Mapped[int] = mapped_column(Integer, ForeignKey("shifts.id"), nullable=False)
    json_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


# --- Split Bill ---

class SplitSession(Base):
    __tablename__ = "split_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    total_ways: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[SplitSessionStatus] = mapped_column(
        Enum(SplitSessionStatus, values_callable=lambda values: [status.value for status in values], validate_strings=True),
        nullable=False,
        default=SplitSessionStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    shares: Mapped[List["SplitShare"]] = relationship(
        "SplitShare", back_populates="split_session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_split_sessions_order", "order_id"),
        Index("ix_split_sessions_status", "status"),
    )


class SplitShare(Base):
    __tablename__ = "split_shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    split_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("split_sessions.id", ondelete="CASCADE"), nullable=False
    )
    share_index: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[SplitShareStatus] = mapped_column(
        Enum(SplitShareStatus, values_callable=lambda values: [status.value for status in values], validate_strings=True),
        nullable=False,
        default=SplitShareStatus.UNPAID,
    )
    payment_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    split_session: Mapped["SplitSession"] = relationship("SplitSession", back_populates="shares")

    __table_args__ = (
        Index("ix_split_shares_session", "split_session_id"),
        Index("ix_split_shares_status", "status"),
    )


# --- Inventory ---

class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    low_stock_threshold: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=5)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="pcs")
