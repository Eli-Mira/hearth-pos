"""Operational kitchen display for submitted restaurant orders."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.db.models import Order, OrderStatus
from app.services.orders import OrderError, order_service


class KitchenScreen(QWidget):
    """Display submitted tickets and advance them through cooking and ready states."""

    back_requested = Signal()

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._setup_ui()
        self.refresh_queue()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Kitchen Queue")
        title.setProperty("heading", "true")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_queue)
        header.addWidget(refresh_button)
        back_button = QPushButton("Back")
        back_button.clicked.connect(self.back_requested.emit)
        header.addWidget(back_button)
        layout.addLayout(header)

        self.status_label = QLabel("Loading tickets…")
        self.status_label.setProperty("secondary", "true")
        layout.addWidget(self.status_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.queue_container = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_layout.setSpacing(12)
        self.queue_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.queue_container)
        layout.addWidget(scroll, 1)

    def _clear_queue(self) -> None:
        while self.queue_layout.count():
            item = self.queue_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _next_action(order: Order) -> str:
        return "Start Cooking" if order.status == OrderStatus.SENT_TO_KITCHEN else "Mark Ready"

    def _ticket_widget(self, order: Order) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(6)

        header = QHBoxLayout()
        location = f" · Table {order.table.number}" if order.table is not None else ""
        heading = QLabel(f"Order #{order.id}{location}")
        heading.setStyleSheet("font-size: 18px; font-weight: 700;")
        header.addWidget(heading)
        header.addStretch()
        status_text = "New" if order.status == OrderStatus.SENT_TO_KITCHEN else "Cooking"
        status = QLabel(status_text)
        status.setProperty("secondary", "true")
        header.addWidget(status)
        card_layout.addLayout(header)

        active_items = [item for item in order.items if not item.voided]
        for item in active_items:
            modifiers = ", ".join(modifier.name for modifier in item.modifiers)
            item_text = f"{item.quantity}× {item.name_snapshot}"
            if modifiers:
                item_text += f"  + {modifiers}"
            card_layout.addWidget(QLabel(item_text))

        action = QPushButton(self._next_action(order))
        action.setProperty("primary", "true")
        action.clicked.connect(lambda _checked=False, order_id=order.id: self._advance_ticket(order_id))
        card_layout.addWidget(action)
        return card

    def refresh_queue(self) -> None:
        """Reload the live submitted/cooking queue from the lifecycle service."""
        self._clear_queue()
        try:
            orders = order_service.get_kitchen_queue()
        except Exception as error:
            self.status_label.setText(f"Kitchen queue unavailable: {error}")
            return
        if not orders:
            self.status_label.setText("No tickets waiting.")
            return
        self.status_label.setText(f"{len(orders)} ticket{'s' if len(orders) != 1 else ''} waiting")
        for order in orders:
            self.queue_layout.addWidget(self._ticket_widget(order))

    def _advance_ticket(self, order_id: int) -> None:
        """Advance one ticket then redraw the server-backed queue."""
        try:
            order_service.advance_kitchen_order(self.current_user, order_id)
        except (OrderError, Exception) as error:
            QMessageBox.warning(self, "Kitchen update failed", str(error))
            return
        self.refresh_queue()

    def apply_theme(self, theme_manager) -> None:
        palette = theme_manager._get_palette()
        self.setStyleSheet(
            "KitchenScreen {"
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {palette['bg_gradient_start']}, stop:1 {palette['bg_gradient_end']});"
            "}"
        )
