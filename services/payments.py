"""Payment service for handling payments and checkout."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional, List

from app.db.engine import session_scope
from app.db.repositories import OrderRepository, PaymentRepository, TableRepository
from app.db.models import Order, OrderStatus, Payment, PaymentType, DiningTable, TableStatus
from app.services.orders import order_service
from app.services.auth import auth_service, AuthError
from app.services.money import quantize, calculate_change, add, ZERO
from app.services.audit import audit_service


class PaymentError(Exception):
    pass


class PaymentService:
    def process_payment(self, actor: StaffUser, order_id: int, payment_type: PaymentType,
                        amount: Decimal, tendered: Decimal = ZERO) -> Payment:
        if not auth_service.check_permission(actor, "orders.pay"):
            raise AuthError("Permission denied")
        
        amount = quantize(amount)
        tendered = quantize(tendered)
        
        with session_scope() as session:
            order_repo = OrderRepository(session)
            payment_repo = PaymentRepository(session)
            table_repo = TableRepository(session)

            order = order_repo.get_by_id(order_id)
            if not order:
                raise PaymentError("Order not found")

            # Verify order is ready for payment
            if order.status not in (OrderStatus.BILL_REQUESTED, OrderStatus.READY, OrderStatus.SENT_TO_KITCHEN):
                raise PaymentError("Order not ready for payment")

            # Get total due
            summary = order_service.get_order_summary(order_id, session=session)
            total_due = summary["total"]
            paid_so_far = payment_repo.get_total_paid(order_id)
            remaining = quantize(total_due - paid_so_far)
            
            if amount > remaining:
                raise PaymentError(f"Payment amount ${amount} exceeds remaining balance ${remaining}")
            
            # Calculate change for cash payments
            change = ZERO
            if payment_type == PaymentType.CASH:
                if tendered < amount:
                    raise PaymentError(f"Tendered amount ${tendered} is less than payment amount ${amount}")
                change = calculate_change(tendered, amount)
            
            # For card_manual, tendered = amount (no change)
            if payment_type == PaymentType.CARD_MANUAL:
                tendered = amount
            
            payment = payment_repo.add_payment(
                order_id=order_id,
                payment_type=payment_type,
                amount=amount,
                tendered=tendered,
                change=change,
                created_by=actor.id,
            )
            
            # Check if fully paid
            new_paid = add(paid_so_far, amount)
            if new_paid >= total_due:
                order_repo.update_status(order_id, OrderStatus.PAID)
                
                # Update table status
                if order.table_id:
                    table_repo.update_status(order.table_id, TableStatus.DIRTY)
            
            audit_service.log(
                actor.id, "payment_processed", "payment", payment.id,
                {
                    "order_id": order_id,
                    "payment_type": payment_type.value,
                    "amount": str(amount),
                    "tendered": str(tendered),
                    "change": str(change),
                    "fully_paid": new_paid >= total_due,
                }
            )
            
            return payment
    
    def get_payments_for_order(self, order_id: int) -> List[Payment]:
        with session_scope() as session:
            return PaymentRepository(session).get_for_order(order_id)
    
    def get_checkout_summary(self, order_id: int) -> dict:
        """Get payment summary for checkout screen."""
        # Reuse the canonical order summary from OrderService to avoid duplication.
        from app.services.orders import order_service
        with session_scope() as session:
            summary = order_service.get_order_summary(order_id, session=session)
            if not summary:
                return {}
            
            payment_repo = PaymentRepository(session)
            order = summary["order"]
            total_due = summary["total"]
            paid_so_far = payment_repo.get_total_paid(order_id)
            remaining = quantize(total_due - paid_so_far)
            payments = payment_repo.get_for_order(order_id)
            
            return {
                "order": order,
                "subtotal": summary["subtotal"],
                "tax_total": summary["tax_total"],
                "total": total_due,
                "paid": paid_so_far,
                "remaining": remaining,
                "payments": payments,
                "is_fully_paid": remaining <= ZERO,
            }
    
    # _get_order_summary removed — now lives in OrderService.get_order_summary()


payment_service = PaymentService()