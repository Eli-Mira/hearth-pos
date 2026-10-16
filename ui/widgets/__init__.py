"""Custom UI widgets for the POS."""
from __future__ import annotations

from decimal import Decimal
from typing import Optional, Callable, List

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QPushButton, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QSizePolicy
)
from PySide6.QtGui import QFont, QPalette, QColor

from app.db.models import MenuItem, DiningTable, TableStatus, OrderItem
from app.ui.widgets.navigation import AppTopBar
from app.ui.widgets.component_library import BaseTile, StatefulButton, ProgressBar, Card, Badge, QuickAction, DataTable
from app.ui.widgets.table_management import TableManagementDialog


class PinPadButton(QPushButton):
    """Large PIN pad button."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("PinPadButton")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(QSize(80, 80))
        
        font = QFont("Inter", 28, QFont.Weight.Bold)
        self.setFont(font)


class NumPadButton(QPushButton):
    """Numpad button for checkout."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("NumPadButton")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(QSize(64, 64))
        
        font = QFont("Inter", 24, QFont.Weight.Medium)
        self.setFont(font)


class PinPadWidget(QWidget):
    """PIN entry widget with large buttons."""
    
    pin_entered = Signal(str)  # Emitted when 4-6 digits entered
    pin_cleared = Signal()
    backspace_pressed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pin = ""
        self._max_length = 6
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # PIN display
        self.pin_display = QLabel("●" * 0)
        self.pin_display.setAlignment(Qt.AlignCenter)
        self.pin_display.setObjectName("pinDisplay")
        self.pin_display.setStyleSheet("""
            QLabel#pinDisplay {
                font-size: 36px;
                letter-spacing: 24px;
                padding: 20px;
                color: @text-primary;
            }
        """)
        layout.addWidget(self.pin_display, 0, 0, 1, 3)
        
        # Number buttons 1-9
        buttons = [
            ("1", 1, 0), ("2", 1, 1), ("3", 1, 2),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2),
            ("7", 3, 0), ("8", 3, 1), ("9", 3, 2),
            ("⌫", 4, 0), ("0", 4, 1), ("✓", 4, 2),
        ]
        
        for text, row, col in buttons:
            btn = PinPadButton(text)
            if text == "⌫":
                btn.clicked.connect(self._on_backspace)
                btn.setStyleSheet("PinPadButton { background-color: @surface; } PinPadButton:hover { background-color: @warn; }")
            elif text == "✓":
                btn.clicked.connect(self._on_confirm)
                btn.setStyleSheet("PinPadButton { background-color: @ok; } PinPadButton:hover { background-color: #358E5E; }")
            else:
                btn.clicked.connect(lambda checked, t=text: self._on_digit(t))
            layout.addWidget(btn, row, col)
    
    def _on_digit(self, digit: str):
        if len(self._pin) < self._max_length:
            self._pin += digit
            self._update_display()
    
    def _on_backspace(self):
        if self._pin:
            self._pin = self._pin[:-1]
            self._update_display()
        else:
            self.pin_cleared.emit()
    
    def _on_confirm(self):
        if len(self._pin) >= 4:
            self.pin_entered.emit(self._pin)
    
    def _update_display(self):
        self.pin_display.setText("●" * len(self._pin))
    
    def clear(self):
        self._pin = ""
        self._update_display()
    
    def set_max_length(self, length: int):
        self._max_length = length


class NumPadWidget(QWidget):
    """Numeric keypad for amount entry."""
    
    digit_pressed = Signal(str)
    backspace_pressed = Signal()
    clear_pressed = Signal()
    confirm_pressed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        buttons = [
            ("7", 0, 0), ("8", 0, 1), ("9", 0, 2), ("C", 0, 3),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2), ("⌫", 1, 3),
            ("1", 2, 0), ("2", 2, 1), ("3", 2, 2), (".", 2, 3),
            ("0", 3, 0), ("00", 3, 1), ("", 3, 2), ("✓", 3, 3),
        ]
        
        for text, row, col in buttons:
            if text == "":
                continue
            btn = NumPadButton(text)
            if text == "C":
                btn.clicked.connect(self.clear_pressed.emit)
                btn.setStyleSheet("NumPadButton { background-color: @err; } NumPadButton:hover { background-color: #C44A4A; }")
            elif text == "⌫":
                btn.clicked.connect(self.backspace_pressed.emit)
            elif text == "✓":
                btn.clicked.connect(self.confirm_pressed.emit)
                btn.setStyleSheet("NumPadButton { background-color: @ok; } NumPadButton:hover { background-color: #358E5E; }")
            else:
                btn.clicked.connect(lambda checked, t=text: self.digit_pressed.emit(t))
            layout.addWidget(btn, row, col)


class MenuTile(QFrame):
    """Menu item tile for the order screen."""
    
    clicked = Signal(object)  # Emits MenuItem
    
    def __init__(self, menu_item: MenuItem, parent=None):
        super().__init__(parent)
        self.menu_item = menu_item
        self.setObjectName("MenuTile")
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(QSize(160, 120))
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._selected = False
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Name
        self.name_label = QLabel(self.menu_item.name)
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignCenter)
        font = QFont("Inter", 16, QFont.Weight.Medium)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label)
        
        # Price
        self.price_label = QLabel(f"${self.menu_item.price:.2f}")
        self.price_label.setAlignment(Qt.AlignCenter)
        font = QFont("Inter", 18, QFont.Weight.Bold)
        self.price_label.setFont(font)
        self.price_label.setStyleSheet("color: @accent;")
        layout.addWidget(self.price_label)
        
        # Modifier indicator
        if self.menu_item.modifiers:
            self.mod_label = QLabel(f"{len(self.menu_item.modifiers)} modifiers")
            self.mod_label.setAlignment(Qt.AlignCenter)
            self.mod_label.setStyleSheet("color: @text-secondary; font-size: 12px;")
            layout.addWidget(self.mod_label)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.menu_item)
        super().mousePressEvent(event)
    
    def set_selected(self, selected: bool):
        self._selected = selected
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)


class TableCell(QFrame):
    """Table cell for floor plan view."""
    
    clicked = Signal(object)  # Emits DiningTable
    
    def __init__(self, table: DiningTable, parent=None):
        super().__init__(parent)
        self.table = table
        self.setObjectName("TableCell")
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(QSize(140, 120))
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._setup_ui()
        self._update_status_style()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Table number/name
        self.name_label = QLabel(self.table.name)
        self.name_label.setAlignment(Qt.AlignCenter)
        font = QFont("Inter", 18, QFont.Weight.Bold)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label)
        
        # Status
        self.status_label = QLabel(self.table.status.value.replace("_", " ").title())
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setProperty("status", "true")
        layout.addWidget(self.status_label)
        
        # Elapsed time
        self.time_label = QLabel("")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: @text-secondary; font-size: 14px;")
        layout.addWidget(self.time_label)
        
        # Order total (if seated)
        self.total_label = QLabel("")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.total_label.setStyleSheet("color: @accent; font-size: 16px; font-weight: 600; font-variant-numeric: tabular-nums;")
        layout.addWidget(self.total_label)
    
    def _update_status_style(self):
        status_map = {
            TableStatus.OPEN: "ok",
            TableStatus.SEATED: "warning",
            TableStatus.ORDERED: "warn",
            TableStatus.BILL_REQUESTED: "err",
            TableStatus.DIRTY: "err",
        }
        status_type = status_map.get(self.table.status, "ok")
        self.status_label.setProperty("statusType", status_type)
        self.setProperty("status", self.table.status.value)
        self.style().unpolish(self)
        self.style().polish(self)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
    
    def update_status(self, status: TableStatus, elapsed_text: str = "", total_text: str = ""):
        self.table.status = status
        self.status_label.setText(status.value.replace("_", " ").title())
        self._update_status_style()
        self.time_label.setText(elapsed_text)
        self.total_label.setText(total_text)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.table)
        super().mousePressEvent(event)


class OrderItemWidget(QFrame):
    """Widget for displaying an order item in the ticket panel."""
    
    qty_changed = Signal(int)  # new quantity
    remove_requested = Signal()
    modifiers_requested = Signal()
    
    def __init__(self, order_item: OrderItem, parent=None):
        super().__init__(parent)
        self.order_item = order_item
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("OrderItemWidget")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Quantity controls
        self.minus_btn = QPushButton("−")
        self.minus_btn.setFixedSize(QSize(44, 44))
        self.minus_btn.setObjectName("qtyButton")
        self.minus_btn.clicked.connect(lambda: self.qty_changed.emit(max(1, self.order_item.quantity - 1)))
        layout.addWidget(self.minus_btn)
        
        self.qty_label = QLabel(str(self.order_item.quantity))
        self.qty_label.setAlignment(Qt.AlignCenter)
        self.qty_label.setMinimumWidth(40)
        font = QFont("Inter", 18, QFont.Weight.Bold)
        self.qty_label.setFont(font)
        layout.addWidget(self.qty_label)
        
        self.plus_btn = QPushButton("+")
        self.plus_btn.setFixedSize(QSize(44, 44))
        self.plus_btn.setObjectName("qtyButton")
        self.plus_btn.clicked.connect(lambda: self.qty_changed.emit(self.order_item.quantity + 1))
        layout.addWidget(self.plus_btn)
        
        # Item details
        details = QVBoxLayout()
        details.setSpacing(2)
        
        name_text = self.order_item.name_snapshot
        if self.order_item.voided:
            name_text = f"VOID: {name_text}"
        
        self.name_label = QLabel(name_text)
        self.name_label.setWordWrap(True)
        font = QFont("Inter", 15, QFont.Weight.Medium)
        self.name_label.setFont(font)
        if self.order_item.voided:
            self.name_label.setStyleSheet("color: @err; text-decoration: line-through;")
        details.addWidget(self.name_label)
        
        # Modifiers
        if self.order_item.modifiers:
            mod_text = ", ".join(m.name for m in self.order_item.modifiers)
            self.mod_label = QLabel(mod_text)
            self.mod_label.setStyleSheet("color: @text-secondary; font-size: 13px;")
            self.mod_label.setWordWrap(True)
            details.addWidget(self.mod_label)
        
        layout.addLayout(details, 1)
        
        # Price
        line_total = self.order_item.unit_price * self.order_item.quantity
        self.price_label = QLabel(f"${line_total:.2f}")
        self.price_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        font = QFont("Inter", 16, QFont.Weight.Bold)
        self.price_label.setFont(font)
        self.price_label.setMinimumWidth(80)
        layout.addWidget(self.price_label)
        
        # Action buttons
        self.mod_btn = QPushButton("Mods")
        self.mod_btn.setFixedHeight(44)
        self.mod_btn.clicked.connect(self.modifiers_requested.emit)
        layout.addWidget(self.mod_btn)
        
        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(QSize(44, 44))
        self.remove_btn.setProperty("danger", "true")
        self.remove_btn.clicked.connect(self.remove_requested.emit)
        layout.addWidget(self.remove_btn)
    
    def update_qty(self, qty: int):
        self.order_item.quantity = qty
        self.qty_label.setText(str(qty))
        line_total = self.order_item.unit_price * qty
        self.price_label.setText(f"${line_total:.2f}")


class AmountDisplay(QWidget):
    """Large amount display for checkout."""
    
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(label)
        self.label.setProperty("subheading", "true")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)
        
        self.amount = QLabel("$0.00")
        self.amount.setProperty("total", "true")
        self.amount.setAlignment(Qt.AlignRight)
        layout.addWidget(self.amount)
    
    def set_amount(self, amount: Decimal):
        self.amount.setText(f"${amount:.2f}")


class StatusIndicator(QWidget):
    """Colored status indicator with label."""
    
    def __init__(self, text: str, status_type: str = "ok", parent=None):
        super().__init__(parent)
        self.status_type = status_type
        
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self.indicator = QLabel("●")
        self.indicator.setFixedSize(QSize(16, 16))
        layout.addWidget(self.indicator)
        
        self.label = QLabel(text)
        font = QFont("Inter", 13, QFont.Weight.Medium)
        self.label.setFont(font)
        layout.addWidget(self.label)
        
        self._update_style()
    
    def _update_style(self):
        colors = {
            "ok": ("@ok", "white"),
            "warn": ("@warn", "@text-primary"),
            "err": ("@err", "white"),
            "info": ("@accent", "white"),
        }
        bg, fg = colors.get(self.status_type, ("@text-secondary", "white"))
        self.indicator.setStyleSheet(f"color: {bg}; font-size: 16px;")
        self.label.setStyleSheet(f"color: {fg};")
    
    def set_status(self, status_type: str, text: str):
        self.status_type = status_type
        self.label.setText(text)
        self._update_style()
