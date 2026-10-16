"""Shift service for cash management and reconciliation."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.db.engine import session_scope
from app.db.repositories import ShiftRepository, PaymentRepository, OrderRepository, AuditRepository
from app.db.models import Shift, Payment, PaymentType, Order, OrderStatus, StaffUser
from app.services.auth import auth_service, AuthError
from app.services.money import quantize, add, ZERO
from app.services.audit import audit_service
from app.config import settings


class ShiftError(Exception):
    pass


class ShiftService:
    def get_current_shift(self) -> Optional[Shift]:
        with session_scope() as session:
            return ShiftRepository(session).get_current_open()
    
    def open_shift(self, actor: StaffUser, opening_float: Optional[Decimal] = None) -> Shift:
        if not auth_service.check_permission(actor, "shifts.manage"):
            raise AuthError("Permission denied")
        
        # Check if shift already open
        current = self.get_current_shift()
        if current:
            raise ShiftError("A shift is already open")
        
        float_amount = opening_float or settings.default_float_amount
        float_amount = quantize(float_amount)
        
        with session_scope() as session:
            shift = ShiftRepository(session).open_shift(actor.id, float_amount)
            audit_service.log(
                actor.id, "shift_opened", "shift", shift.id,
                {"opening_float": str(float_amount)}
            )
            return shift
    
    def close_shift(self, actor: StaffUser, counted_cash: Decimal, 
                    manager_signoff: bool = False) -> Shift:
        if not auth_service.check_permission(actor, "shifts.manage"):
            raise AuthError("Permission denied")
        
        counted_cash = quantize(counted_cash)
        
        with session_scope() as session:
            shift_repo = ShiftRepository(session)
            payment_repo = PaymentRepository(session)
            order_repo = OrderRepository(session)
            
            shift = shift_repo.get_current_shift()
            if not shift:
                raise ShiftError("No open shift to close")
            
            # Calculate expected cash: opening float + cash payments in this shift
            cash_payments = session.query(Payment).join(Order).filter(
                Payment.payment_type == PaymentType.CASH,
                Payment.paid_at >= shift.opened_at,
                Order.status.in_([OrderStatus.PAID, OrderStatus.CLOSED])
            ).all()
            
            cash_sales = ZERO
            for p in cash_payments:
                cash_sales = add(cash_sales, p.amount)
            
            expected = add(shift.opening_float, cash_sales)
            shift_repo.update_expected(shift.id, expected)
            
            variance = quantize(counted_cash - expected)
            needs_signoff = abs(variance) > Decimal("0.01")  # Any variance needs signoff
            
            signoff_by = actor.id if (actor.role.value == "manager" or manager_signoff) else None
            if needs_signoff and not signoff_by:
                raise AuthError(f"Cash variance ${variance} requires manager sign-off")
            
            closed_shift = shift_repo.close_shift(shift.id, counted_cash, signoff_by)
            if not closed_shift:
                raise ShiftError("Failed to close shift")
            
            closed_shift.variance = variance
            
            audit_service.log(
                actor.id, "shift_closed", "shift", shift.id,
                {
                    "opening_float": str(shift.opening_float),
                    "cash_sales": str(cash_sales),
                    "expected": str(expected),
                    "counted": str(counted_cash),
                    "variance": str(variance),
                    "manager_signoff": signoff_by is not None,
                }
            )
            
            return closed_shift
    
    def get_shift_summary(self, shift_id: int) -> dict:
        with session_scope() as session:
            shift_repo = ShiftRepository(session)
            payment_repo = PaymentRepository(session)
            order_repo = OrderRepository(session)
            
            shift = shift_repo.get_by_id(shift_id)
            if not shift:
                return {}
            
            # Get all payments in shift time range
            payments = session.query(Payment).filter(
                Payment.paid_at >= shift.opened_at
            )
            if shift.closed_at:
                payments = payments.filter(Payment.paid_at <= shift.closed_at)
            payments = payments.all()
            
            cash_total = ZERO
            card_total = ZERO
            for p in payments:
                if p.payment_type == PaymentType.CASH:
                    cash_total = add(cash_total, p.amount)
                else:
                    card_total = add(card_total, p.amount)
            
            # Order counts
            orders = session.query(Order).filter(
                Order.created_at >= shift.opened_at
            )
            if shift.closed_at:
                orders = orders.filter(Order.created_at <= shift.closed_at)
            order_count = orders.count()
            
            return {
                "shift": shift,
                "cash_total": cash_total,
                "card_total": card_total,
                "total_sales": add(cash_total, card_total),
                "order_count": order_count,
                "expected_cash": shift.closing_expected,
                "counted_cash": shift.closing_counted,
                "variance": shift.variance,
            }


shift_service = ShiftService()