"""Checkout screen for recording cash and manual-card payments."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.hardware.escpos import EscposReceiptPrinter
from app.hardware.fake import fake_receipt_printer
from app.hardware.interfaces import ReceiptData, ReceiptItem, ReceiptPayment

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.db.models import Order, PaymentType
from app.services.auth import AuthError
from app.services.payments import PaymentError, payment_service


class CheckoutScreen(QWidget):
    """Display the outstanding balance and settle it with cash or card."""

    back_requested = Signal()
    payment_completed = Signal(object)

    def __init__(self, current_user, order: Order, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.order = order
        self._setup_ui()
        self.refresh_summary()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        title = QLabel(f"Checkout · Order {self.order.id or 'new'}")
        title.setProperty("heading", "true")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        layout.addWidget(title)

        self.status_label = QLabel()
        self.status_label.setProperty("secondary", "true")
        layout.addWidget(self.status_label)

        summary_frame = QFrame()
        summary_layout = QFormLayout(summary_frame)
        self.subtotal_label = QLabel("$0.00")
        self.tax_label = QLabel("$0.00")
        self.total_label = QLabel("$0.00")
        self.paid_label = QLabel("$0.00")
        self.remaining_label = QLabel("$0.00")
        summary_layout.addRow("Subtotal", self.subtotal_label)
        summary_layout.addRow("Tax", self.tax_label)
        summary_layout.addRow("Total", self.total_label)
        summary_layout.addRow("Paid", self.paid_label)
        summary_layout.addRow("Remaining", self.remaining_label)
        layout.addWidget(summary_frame)

        payment_form = QFormLayout()
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount to pay")
        self.tendered_input = QLineEdit()
        self.tendered_input.setPlaceholderText("Cash received")
        payment_form.addRow("Amount", self.amount_input)
        payment_form.addRow("Tendered", self.tendered_input)
        layout.addLayout(payment_form)

        actions = QHBoxLayout()
        self.cash_button = QPushButton("Pay Cash")
        self.cash_button.setProperty("primary", "true")
        self.cash_button.clicked.connect(lambda: self._process_payment(PaymentType.CASH))
        actions.addWidget(self.cash_button)
        self.card_button = QPushButton("Pay Card")
        self.card_button.clicked.connect(lambda: self._process_payment(PaymentType.CARD_MANUAL))
        actions.addWidget(self.card_button)
        actions.addStretch()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.back_requested.emit)
        actions.addWidget(self.back_button)
        layout.addLayout(actions)
        layout.addStretch()

    def refresh_summary(self) -> None:
        """Reload settlement totals without assuming the passed order is persisted."""
        if self.order.id is None:
            self.status_label.setText("Order must be saved before checkout.")
            self.cash_button.setEnabled(False)
            self.card_button.setEnabled(False)
            return
        summary = payment_service.get_checkout_summary(self.order.id)
        if not summary:
            self.status_label.setText("Order could not be loaded.")
            self.cash_button.setEnabled(False)
            self.card_button.setEnabled(False)
            return
        self.order = summary["order"]
        self.subtotal_label.setText(f"${summary['subtotal']:.2f}")
        self.tax_label.setText(f"${summary['tax_total']:.2f}")
        self.total_label.setText(f"${summary['total']:.2f}")
        self.paid_label.setText(f"${summary['paid']:.2f}")
        self.remaining_label.setText(f"${summary['remaining']:.2f}")
        self.status_label.setText("Paid in full" if summary["is_fully_paid"] else "Payment required")
        self.cash_button.setEnabled(not summary["is_fully_paid"])
        self.card_button.setEnabled(not summary["is_fully_paid"])
        if not self.amount_input.text():
            self.amount_input.setText(f"{summary['remaining']:.2f}")

    def _process_payment(self, payment_type: PaymentType) -> None:
        try:
            amount = Decimal(self.amount_input.text().strip())
            tendered = (
                Decimal(self.tendered_input.text().strip())
                if payment_type == PaymentType.CASH and self.tendered_input.text().strip()
                else amount
            )
        except (InvalidOperation, ValueError):
            QMessageBox.warning(self, "Invalid amount", "Enter valid decimal payment amounts.")
            return

        try:
            payment = payment_service.process_payment(
                self.current_user, self.order.id, payment_type, amount, tendered
            )
        except (PaymentError, AuthError) as error:
            QMessageBox.warning(self, "Payment not recorded", str(error))
            return

        self.refresh_summary()
        if payment.change:
            QMessageBox.information(self, "Change", f"Return ${payment.change:.2f}.")
        if not self.cash_button.isEnabled():
            self._print_receipt()
            self.payment_completed.emit(self.order)

    def _print_receipt(self) -> None:
        """Print the settled order, retaining a software fallback when hardware is offline."""
        if self.order.id is None:
            return
        summary = payment_service.get_checkout_summary(self.order.id)
        if not summary:
            return

        order = summary["order"]
        items = [
            ReceiptItem(
                name=item.name_snapshot,
                qty=item.quantity,
                unit_price=item.unit_price,
                line_total=item.total_price,
                modifiers=[modifier.name for modifier in item.modifiers],
                voided=item.voided,
            )
            for item in order.items
            if not item.voided
        ]
        payments = [
            ReceiptPayment(
                payment_type=payment.payment_type.value,
                amount=payment.amount,
                tendered=payment.tendered or payment.amount,
                change=payment.change or Decimal("0.00"),
            )
            for payment in summary["payments"]
        ]
        receipt = ReceiptData(
            venue_name="HEARTH",
            order_id=order.id,
            order_type=order.order_type.value,
            table_number=None,
            server_name=self.current_user.name,
            timestamp=order.created_at.strftime("%Y-%m-%d %I:%M %p"),
            items=items,
            subtotal=summary["subtotal"],
            tax_total=summary["tax_total"],
            total=summary["total"],
            payments=payments,
        )
        try:
            printed = EscposReceiptPrinter().print_receipt(receipt)
        except Exception:
            printed = False
        if not printed:
            fake_receipt_printer.print_receipt(receipt)

    def apply_theme(self, theme_manager) -> None:
        palette = theme_manager._get_palette()
        self.setStyleSheet(
            "CheckoutScreen {"
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {palette['bg_gradient_start']}, stop:1 {palette['bg_gradient_end']});"
            "}"
        )
