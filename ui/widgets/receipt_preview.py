"""Receipt preview widget with Lain-themed status bar."""
from __future__ import annotations

from decimal import Decimal
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
)
from PySide6.QtGui import QFont

from app.hardware.interfaces import ReceiptData, ReceiptItem, ReceiptPayment


class ReceiptPreview(QFrame):
    """Receipt preview with styled status bar and thermal-paper look."""
    
    def __init__(self, receipt: ReceiptData, parent=None):
        super().__init__(parent)
        self.setObjectName("ReceiptPreview")
        self._setup_ui(receipt)
    
    def _setup_ui(self, receipt: ReceiptData):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Status bar
        status_bar = QFrame()
        status_bar.setObjectName("ReceiptStatusBar")
        status_bar.setStyleSheet("""
            QFrame#ReceiptStatusBar {
                background-color: @status_bar_bg;
                border-radius: 8px;
                padding: 10px 16px;
            }
            QLabel { color: @status_bar_strong; font-weight: 700; }
        """)
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(12, 8, 12, 8)
        status_layout.setSpacing(12)
        
        status_icon = QLabel("✓")
        status_icon.setStyleSheet("color: @status_bar_good; font-size: 20px; font-weight: 700;")
        status_layout.addWidget(status_icon)
        
        status_text = QLabel("PAYMENT COMPLETE")
        status_text.setProperty("receiptStatus", "success")
        status_text.setStyleSheet("font-size: 15px; font-weight: 700;")
        status_layout.addWidget(status_text)
        
        status_layout.addStretch()
        
        status_amount = QLabel(f"TOTAL: ${receipt.total:.2f}")
        status_amount.setStyleSheet("font-size: 15px; font-weight: 700;")
        status_layout.addWidget(status_amount)
        
        layout.addWidget(status_bar)
        
        # Receipt body
        body = QFrame()
        body_layout = QVBoxLayout(body)
        body_layout.setSpacing(6)
        body_layout.setContentsMargins(20, 20, 20, 20)
        
        # Venue
        venue = QLabel(receipt.venue_name)
        venue.setAlignment(Qt.AlignCenter)
        venue.setFont(QFont("Inter", 18, QFont.Weight.Bold))
        venue.setStyleSheet("color: #111827; padding: 8px;")
        body_layout.addWidget(venue)
        
        # Order info
        info = QLabel(f"Order #{receipt.order_id}  •  {receipt.timestamp}")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #374151; font-size: 12px; font-family: monospace; padding: 4px;")
        body_layout.addWidget(info)
        
        # Divider
        self._add_divider(body_layout)
        
        # Items
        for item in receipt.items:
            item_row = QHBoxLayout()
            
            qty_name = QLabel(f"{item.qty}x {item.name}")
            qty_name.setStyleSheet("font-size: 13px; color: #111827;")
            item_row.addWidget(qty_name)
            
            item_row.addStretch()
            
            line_total = QLabel(f"${item.line_total:.2f}")
            line_total.setStyleSheet("font-size: 13px; font-weight: 600; color: #111827; font-family: monospace;")
            item_row.addWidget(line_total)
            
            body_layout.addLayout(item_row)
            
            if item.modifiers:
                mod_label = QLabel("    + " + ", ".join(item.modifiers))
                mod_label.setStyleSheet("font-size: 11px; color: #6B7280; font-style: italic;")
                body_layout.addWidget(mod_label)
        
        # Divider
        self._add_divider(body_layout)
        
        # Totals
        subtotal_row = QHBoxLayout()
        subtotal_row.addWidget(QLabel("Subtotal"))
        subtotal_row.addStretch()
        subtotal_row.addWidget(QLabel(f"${receipt.subtotal:.2f}"))
        body_layout.addLayout(subtotal_row)
        
        tax_row = QHBoxLayout()
        tax_row.addWidget(QLabel("Tax"))
        tax_row.addStretch()
        tax_row.addWidget(QLabel(f"${receipt.tax_total:.2f}"))
        body_layout.addLayout(tax_row)
        
        total_row = QHBoxLayout()
        total_lbl = QLabel("TOTAL")
        total_lbl.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        total_row.addWidget(total_lbl)
        total_row.addStretch()
        total_val = QLabel(f"${receipt.total:.2f}")
        total_val.setFont(QFont("Inter", 14, QFont.Weight.Bold))
        total_val.setStyleSheet("color: #111827;")
        total_row.addWidget(total_val)
        body_layout.addLayout(total_row)
        
        # Divider
        self._add_divider(body_layout)
        
        # Payments
        for payment in receipt.payments:
            pay_row = QHBoxLayout()
            pay_icon = QLabel({
                "cash": "💵",
                "card_manual": "💳",
            }.get(payment.payment_type, "💰"))
            pay_row.addWidget(pay_icon)
            
            pay_label = QLabel(payment.payment_type.replace("_", " ").title())
            pay_label.setStyleSheet("font-size: 13px; color: #111827;")
            pay_row.addWidget(pay_label)
            
            pay_row.addStretch()
            pay_val = QLabel(f"${payment.amount:.2f}")
            pay_val.setStyleSheet("font-size: 13px; font-weight: 600; font-family: monospace; color: #111827;")
            pay_row.addWidget(pay_val)
            
            body_layout.addLayout(pay_row)
            
            if payment.tendered > 0:
                change_row = QHBoxLayout()
                change_row.addWidget(QLabel("  Change"))
                change_row.addStretch()
                change_val = QLabel(f"${payment.change:.2f}")
                change_val.setStyleSheet("font-size: 13px; font-weight: 600; color: #1B8A4A; font-family: monospace;")
                change_row.addWidget(change_val)
                body_layout.addLayout(change_row)
        
        # Footer
        footer = QLabel("Thank you for dining with us!")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #6B7280; font-size: 12px; padding: 12px; font-style: italic;")
        body_layout.addWidget(footer)
        
        layout.addWidget(body)
    
    def _add_divider(self, layout):
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #D1D5DB; border: none; margin: 6px 0;")
        layout.addWidget(divider)
