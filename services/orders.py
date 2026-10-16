"""Order service for the persisted POS order lifecycle."""
from __future__ import annotations

from decimal import Decimal, ROUND_DOWN
from typing import Iterable, Optional

from sqlalchemy.orm import Session, selectinload

from app.db.engine import session_scope
from app.db.models import (
    DiningTable,
    MenuItem,
    Modifier,
    Order,
    OrderItem,
    OrderStatus,
    OrderType,
    SplitSession,
    SplitSessionStatus,
    SplitShare,
    SplitShareStatus,
    StaffUser,
    TableStatus,
)
from app.config import settings
from app.services.money import quantize
from app.services.auth import auth_service, AuthError


class OrderError(Exception):
    """Raised when an order lifecycle operation is invalid."""


class OrderService:
    """Create and mutate orders using one database transaction per action."""

    def create_order(
        self,
        actor: StaffUser,
        order_type: OrderType,
        table_id: Optional[int] = None,
        guest_count: Optional[int] = None,
    ) -> Order:
        if order_type == OrderType.DINE_IN and table_id is None:
            raise OrderError("A dine-in order requires a table")
        if actor is None or actor.id is None:
            raise OrderError("A persisted staff user is required")

        with session_scope() as session:
            table = None
            if table_id is not None:
                table = session.get(DiningTable, table_id)
                if table is None or table.is_deleted:
                    raise OrderError("Table not found")
                if table.status == TableStatus.DIRTY:
                    raise OrderError("Table must be cleaned before opening an order")

            order = Order(actor_id=actor.id, order_type=order_type, table_id=table_id)
            session.add(order)
            if table is not None and table.status == TableStatus.OPEN:
                table.status = TableStatus.SEATED
            session.flush()
            return (
                session.query(Order)
                .options(selectinload(Order.items).selectinload(OrderItem.modifiers))
                .filter(Order.id == order.id)
                .one()
            )

    def get_active_for_table(self, table_id: int) -> Optional[Order]:
        active_statuses = (
            OrderStatus.OPEN,
            OrderStatus.HELD,
            OrderStatus.SENT_TO_KITCHEN,
            OrderStatus.IN_PROGRESS,
            OrderStatus.READY,
            OrderStatus.BILL_REQUESTED,
        )
        with session_scope() as session:
            return (
                session.query(Order)
                .options(selectinload(Order.items).selectinload(OrderItem.modifiers))
                .filter(Order.table_id == table_id, Order.status.in_(active_statuses))
                .order_by(Order.id.desc())
                .first()
            )

    def add_item(
        self,
        actor: StaffUser,
        order_id: int,
        menu_item_id: int,
        qty: int = 1,
        modifier_ids: Optional[Iterable[int]] = None,
    ) -> OrderItem:
        """Compatibility façade for ID-based callers of order entry."""
        if not auth_service.check_permission(actor, "orders.modify"):
            raise AuthError("Permission denied")
        with session_scope() as session:
            order = session.get(Order, order_id)
            menu_item = session.get(MenuItem, menu_item_id)
            if order is None:
                raise OrderError("Order not found")
            if menu_item is None:
                raise OrderError("Menu item not found")
            modifiers = []
            if modifier_ids:
                modifiers = list(
                    session.query(Modifier).filter(Modifier.id.in_(list(modifier_ids))).all()
                )
        return self.add_item_to_order(order, menu_item, quantity=qty, modifiers=modifiers)

    def add_item_to_order(
        self,
        order: Order,
        menu_item: MenuItem,
        quantity: int = 1,
        modifiers: Optional[Iterable[Modifier]] = None,
    ) -> OrderItem:
        if order is None or order.id is None:
            raise OrderError("A persisted order is required")
        if menu_item is None or menu_item.id is None:
            raise OrderError("A persisted menu item is required")
        if quantity < 1:
            raise OrderError("Quantity must be at least one")

        modifier_ids = [modifier.id for modifier in (modifiers or []) if modifier.id is not None]
        with session_scope() as session:
            persisted_order = session.get(Order, order.id)
            persisted_item = (
                session.query(MenuItem)
                .options(selectinload(MenuItem.category))
                .filter(MenuItem.id == menu_item.id, MenuItem.is_deleted.is_(False))
                .one_or_none()
            )
            if persisted_order is None:
                raise OrderError("Order not found")
            if persisted_item is None or not persisted_item.is_available:
                raise OrderError("Menu item is unavailable")
            if persisted_order.status not in (OrderStatus.OPEN, OrderStatus.HELD):
                raise OrderError("Items can only be added to open or held orders")
            if persisted_item.category is None:
                raise OrderError("Menu item must belong to a category")

            selected_modifiers = []
            if modifier_ids:
                selected_modifiers = (
                    session.query(Modifier)
                    .filter(
                        Modifier.id.in_(modifier_ids),
                        Modifier.menu_item_id == persisted_item.id,
                        Modifier.is_deleted.is_(False),
                    )
                    .all()
                )
                if len(selected_modifiers) != len(set(modifier_ids)):
                    raise OrderError("One or more modifiers do not belong to this menu item")

            modifier_total = sum((modifier.price_modifier for modifier in selected_modifiers), Decimal("0.00"))
            unit_price = quantize(persisted_item.price + modifier_total)
            tax_rate = Decimal(persisted_item.category.tax_rate_bps) / Decimal("10000")
            unit_base = quantize(unit_price / (Decimal("1.00") + tax_rate))
            unit_tax = quantize(unit_price - unit_base)
            order_item = OrderItem(
                order_id=persisted_order.id,
                menu_item_id=persisted_item.id,
                category_id=persisted_item.category_id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=quantize(unit_price * quantity),
                name_snapshot=persisted_item.name,
                unit_base=unit_base,
                unit_tax=unit_tax,
                tax_rate_bps=persisted_item.category.tax_rate_bps,
            )
            order_item.modifiers.extend(selected_modifiers)
            session.add(order_item)
            if persisted_order.table is not None:
                persisted_order.table.status = TableStatus.ORDERED
            session.flush()
            session.refresh(order_item)
            # Materialize the relationship before the scoped session closes.
            list(order_item.modifiers)
            return order_item

    def remove_item_from_order(self, order: Order, order_item_id: int) -> bool:
        with session_scope() as session:
            item = session.query(OrderItem).filter(
                OrderItem.id == order_item_id, OrderItem.order_id == order.id
            ).one_or_none()
            if item is None:
                return False
            session.delete(item)
            return True

    def update_order_item_quantity(self, order: Order, order_item_id: int, quantity: int) -> bool:
        if quantity < 1:
            raise OrderError("Quantity must be at least one")
        with session_scope() as session:
            item = session.query(OrderItem).filter(
                OrderItem.id == order_item_id, OrderItem.order_id == order.id
            ).one_or_none()
            if item is None:
                return False
            item.quantity = quantity
            item.total_price = quantize(item.unit_price * quantity)
            return True

    def update_item_qty(self, actor: StaffUser, item_id: int, qty: int) -> bool:
        """Compatibility façade for changing a persisted ticket line quantity."""
        if not auth_service.check_permission(actor, "orders.modify"):
            raise AuthError("Permission denied")
        with session_scope() as session:
            item = session.get(OrderItem, item_id)
            if item is None:
                return False
            order_id = item.order_id
            if item.voided:
                return False
            if qty < 1:
                raise OrderError("Quantity must be at least one")
            item.quantity = qty
            item.total_price = quantize(item.unit_price * qty)
            session.flush()
            return True

    def request_bill(self, actor: StaffUser, order_id: int) -> Order:
        """Move a submitted/ready order into the payment-ready bill state."""
        if not auth_service.check_permission(actor, "orders.modify"):
            raise AuthError("Permission denied")
        with session_scope() as session:
            order = session.get(Order, order_id)
            if order is None:
                raise OrderError("Order not found")
            if order.status not in (OrderStatus.SENT_TO_KITCHEN, OrderStatus.READY):
                raise OrderError("Order is not ready for a bill")
            order.status = OrderStatus.BILL_REQUESTED
            if order.table is not None:
                order.table.status = TableStatus.BILL_REQUESTED
            session.flush()
            session.refresh(order)
            return order

    def split_bill_evenly(self, order_id: int, ways: int) -> list[Decimal]:
        """Divide the current gross order total into cent-accurate equal shares."""
        if ways < 2:
            raise OrderError("Split requires at least two shares")
        summary = self.get_order_summary(order_id)
        if not summary:
            raise OrderError("Order not found")
        total = summary["total"]
        base_share = (total / ways).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        return [base_share] * (ways - 1) + [quantize(total - base_share * (ways - 1))]

    def create_split_session(self, actor: StaffUser, order_id: int, ways: int) -> SplitSession:
        """Persist a cent-accurate active split session for a bill-ready order."""
        if not auth_service.check_permission(actor, "orders.modify"):
            raise AuthError("Permission denied")
        amounts = self.split_bill_evenly(order_id, ways)
        with session_scope() as session:
            order = session.get(Order, order_id)
            if order is None:
                raise OrderError("Order not found")
            active = session.query(SplitSession).filter(
                SplitSession.order_id == order_id, SplitSession.status == SplitSessionStatus.ACTIVE
            ).one_or_none()
            if active is not None:
                raise OrderError("An active split session already exists")
            split_session = SplitSession(order_id=order_id, total_ways=ways, total_amount=sum(amounts, Decimal("0.00")))
            session.add(split_session)
            session.flush()
            for index, amount in enumerate(amounts):
                session.add(SplitShare(split_session_id=split_session.id, share_index=index, amount=amount))
            session.flush()
            list(split_session.shares)
            return split_session

    def void_item(self, actor: StaffUser, item_id: int, reason: str, manager_override: bool = False) -> bool:
        """Void a line while preventing an unpaid refund liability on active split bills."""
        with session_scope() as session:
            item = session.get(OrderItem, item_id)
            if item is None or item.voided:
                return False
            is_manager = auth_service.check_permission(actor, "orders.void")
            if item.total_price >= settings.void_approval_threshold and not is_manager:
                raise AuthError("Manager approval is required for this void")
            split_session = session.query(SplitSession).filter(
                SplitSession.order_id == item.order_id, SplitSession.status == SplitSessionStatus.ACTIVE
            ).one_or_none()
            if split_session is not None:
                paid = session.query(SplitShare).filter(
                    SplitShare.split_session_id == split_session.id, SplitShare.status == SplitShareStatus.PAID
                ).all()
                paid_total = sum((share.amount for share in paid), Decimal("0.00"))
                remaining_total = sum((line.total_price for line in session.query(OrderItem).filter(
                    OrderItem.order_id == item.order_id, OrderItem.voided.is_(False), OrderItem.id != item.id
                )), Decimal("0.00"))
                if paid_total and remaining_total < paid_total and not (is_manager and manager_override):
                    raise AuthError("Refund would be required; manager override is required")
            item.voided = True
            item.void_reason = reason
            item.void_approved_by = actor.id if is_manager and manager_override else None
            session.flush()
            return True

    def calculate_order_totals(self, order: Order) -> tuple[Decimal, Decimal, Decimal]:
        summary = self.get_order_summary(order.id)
        return summary.get("subtotal", Decimal("0.00")), summary.get("tax_total", Decimal("0.00")), summary.get("total", Decimal("0.00"))

    def get_order_summary(self, order_id: int, session: Optional[Session] = None) -> dict:
        """Return tax-exclusive subtotal, tax, gross total, and loaded order items."""
        if session is not None:
            return self._get_order_summary(session, order_id)
        with session_scope() as owned_session:
            return self._get_order_summary(owned_session, order_id)

    @staticmethod
    def _get_order_summary(session: Session, order_id: int) -> dict:
        order = (
            session.query(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.modifiers))
            .filter(Order.id == order_id)
            .one_or_none()
        )
        if order is None:
            return {}

        subtotal = Decimal("0.00")
        tax_total = Decimal("0.00")
        for item in order.items:
            if item.voided:
                continue
            item_base = quantize(item.unit_base * item.quantity)
            item_tax = quantize(item.unit_tax * item.quantity)
            subtotal += item_base
            tax_total += item_tax
        subtotal = quantize(subtotal)
        tax_total = quantize(tax_total)
        return {
            "order": order,
            "subtotal": subtotal,
            "tax_total": tax_total,
            "total": quantize(subtotal + tax_total),
            "items": order.items,
        }

    def send_to_kitchen(self, actor: StaffUser, order_id: int) -> Order:
        """Submit a non-empty editable order to the kitchen queue."""
        if not auth_service.check_permission(actor, "orders.send_kitchen"):
            raise AuthError("Permission denied")
        with session_scope() as session:
            order = session.get(Order, order_id)
            if order is None:
                raise OrderError(f"Order {order_id} not found")
            if order.status not in (OrderStatus.OPEN, OrderStatus.HELD):
                raise OrderError("Only open or held orders can be sent to the kitchen")
            has_active_items = session.query(OrderItem.id).filter(
                OrderItem.order_id == order_id, OrderItem.voided.is_(False)
            ).first()
            if has_active_items is None:
                raise OrderError("Cannot send an order with no active items")
            order.status = OrderStatus.SENT_TO_KITCHEN
            session.flush()
            session.refresh(order)
            return order

    def get_kitchen_queue(self) -> list[Order]:
        """Return submitted and in-progress orders in first-submitted order."""
        with session_scope() as session:
            return list(
                session.query(Order)
                .options(selectinload(Order.items).selectinload(OrderItem.modifiers), selectinload(Order.table))
                .filter(Order.status.in_((OrderStatus.SENT_TO_KITCHEN, OrderStatus.IN_PROGRESS)))
                .order_by(Order.created_at.asc(), Order.id.asc())
                .all()
            )

    def advance_kitchen_order(self, actor: StaffUser, order_id: int) -> Order:
        """Advance a kitchen ticket from submitted → cooking → ready."""
        if not auth_service.check_permission(actor, "kitchen.update_status"):
            raise AuthError("Permission denied")
        transitions = {
            OrderStatus.SENT_TO_KITCHEN: OrderStatus.IN_PROGRESS,
            OrderStatus.IN_PROGRESS: OrderStatus.READY,
        }
        with session_scope() as session:
            order = session.get(Order, order_id)
            if order is None:
                raise OrderError(f"Order {order_id} not found")
            new_status = transitions.get(order.status)
            if new_status is None:
                raise OrderError("Kitchen order cannot be advanced from its current status")
            order.status = new_status
            session.flush()
            session.refresh(order)
            return order

    def set_order_status(self, order_id: int, new_status: OrderStatus) -> Order:
        with session_scope() as session:
            order = session.get(Order, order_id)
            if order is None:
                raise OrderError(f"Order {order_id} not found")
            order.status = new_status
            if order.table is not None and new_status == OrderStatus.BILL_REQUESTED:
                order.table.status = TableStatus.BILL_REQUESTED
            session.flush()
            session.refresh(order)
            return order


order_service = OrderService()
