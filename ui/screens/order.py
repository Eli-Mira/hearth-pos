"""Order entry screen - main POS workflow."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional, List

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy, QMessageBox,
    QTabWidget, QInputDialog, QLineEdit
)
from PySide6.QtGui import QFont

from app.ui.widgets import (
    MenuTile, OrderItemWidget, AmountDisplay, NumPadWidget,
    StatusIndicator
)
from app.ui.widgets.component_library import get_palette
from app.services.menu import menu_service
from app.services.orders import order_service, OrderError
from app.services.auth import auth_service
from app.db.models import MenuItem, Order, OrderType, OrderStatus, OrderItem, Modifier, StaffUser
from app.db.models import OrderStatus

class OrderScreen(QWidget):
    """Main order entry screen with menu grid and ticket panel."""

    back_requested = Signal()
    checkout_requested = Signal(object)  # Emits Order
    order_sent_to_kitchen = Signal(object)  # Emits Order

    def __init__(self, current_user: StaffUser, order_type: OrderType, table_id: int = None, guest_count: int = None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.order_type = order_type
        self.table_id = table_id
        self.guest_count = guest_count
        self._order: Optional[Order] = None
        self._current_category = None
        self._menu_tiles = []
        self._order_item_widgets = {}
        self._category_scrolls = {}  # category_id -> QScrollArea
        self._category_grids = {}  # category_id -> QGridLayout
        self._setup_ui()
        self._load_or_create_order()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # LEFT PANEL - Menu (62%)
        left_panel = QWidget()
        left_panel.setObjectName("LeftPanel")
        left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(8, 8, 4, 8)

        # Category tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("CategoryTabs")
        self.tab_widget.currentChanged.connect(self._on_category_changed)
        left_layout.addWidget(self.tab_widget)

        # Menu grid in scroll area
        self.menu_scroll = QScrollArea()
        self.menu_scroll.setWidgetResizable(True)
        self.menu_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.menu_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.menu_scroll.setFocusPolicy(Qt.NoFocus)  # Scroll area itself doesn't need focus

        self.menu_container = QWidget()
        self.menu_grid = QGridLayout(self.menu_container)
        self.menu_grid.setSpacing(12)
        self.menu_grid.setContentsMargins(8, 8, 8, 8)

        self.menu_scroll.setWidget(self.menu_container)
        left_layout.addWidget(self.menu_scroll, 1)

        main_layout.addWidget(left_panel, 62)

        # RIGHT PANEL - Ticket (38%)
        right_panel = QFrame()
        right_panel.setObjectName("RightPanel")
        right_panel.setFixedWidth(420)
        right_panel.setStyleSheet("""
            QFrame#RightPanel {
                background-color: @surface;
                border-left: 1px solid @border;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(12, 12, 12, 12)

        # Header with improved structure
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Order identifier with icon
        if self.order_type == OrderType.DINE_IN:
            self.order_title = QLabel(f"🪑 Table {self.table_id}")
        else:
            self.order_title = QLabel(self.order_type.value.replace("_", " ").title())
        self.order_title.setProperty("heading", "true")
        self.order_title.setStyleSheet("font-size: 22px;")
        header_layout.addWidget(self.order_title)

        header_layout.addStretch()

        # Status with colored indicator
        self.order_status = StatusIndicator("New Order", "info")
        header_layout.addWidget(self.order_status)

        right_layout.addLayout(header_layout)

        # Order items list with improved styling
        self.items_scroll = QScrollArea()
        self.items_scroll.setWidgetResizable(True)
        self.items_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.items_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.items_container = QWidget()
        self.items_container.setObjectName("itemsContainer")
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setSpacing(6)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.addStretch()

        self.items_scroll.setWidget(self.items_container)
        right_layout.addWidget(self.items_scroll)

        # Totals with enhanced visibility
        totals_frame = QFrame()
        totals_frame.setObjectName("totalsFrame")
        totals_frame.setStyleSheet("""
            QFrame {
                background-color: @surface-raised;
                border-radius: 14px;
                padding: 16px;
                border: 1px solid @border;
            }
        """)
        totals_layout = QVBoxLayout(totals_frame)
        totals_layout.setSpacing(10)

        self.subtotal_display = AmountDisplay("Subtotal")
        self.subtotal_display.setStyleSheet("")
        totals_layout.addWidget(self.subtotal_display)

        self.tax_display = AmountDisplay("Tax")
        totals_layout.addWidget(self.tax_display)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(2)
        divider.setStyleSheet("background-color: @border; border: none; margin: 4px 0;")
        totals_layout.addWidget(divider)

        self.total_display = AmountDisplay("Total")
        self.total_display.amount.setProperty("total", "true")
        totals_layout.addWidget(self.total_display)

        right_layout.addWidget(totals_frame)

        # Action buttons with improved visual hierarchy
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)

        self.send_kitchen_btn = QPushButton("🖨️  Send to Kitchen")
        self.send_kitchen_btn.setObjectName("sendKitchenBtn")
        self.send_kitchen_btn.setProperty("primary", "true")
        self.send_kitchen_btn.setMinimumHeight(72)
        self.send_kitchen_btn.clicked.connect(self._send_to_kitchen)
        button_layout.addWidget(self.send_kitchen_btn)

        self.checkout_btn = QPushButton("💳  Checkout")
        self.checkout_btn.setProperty("success", "true")
        self.checkout_btn.setMinimumHeight(72)
        self.checkout_btn.clicked.connect(self._go_to_checkout)
        button_layout.addWidget(self.checkout_btn)

        # Hold button
        self.hold_btn = QPushButton("Hold")
        self.hold_btn.setObjectName("holdBtn")
        self.hold_btn.setProperty("secondary", "true")
        self.hold_btn.setMinimumHeight(50)
        self.hold_btn.clicked.connect(self._hold_order)
        button_layout.addWidget(self.hold_btn)

        # Recall button
        self.recall_btn = QPushButton("Recall")
        self.recall_btn.setObjectName("recallBtn")
        self.recall_btn.setProperty("secondary", "true")
        self.recall_btn.setMinimumHeight(50)
        self.recall_btn.clicked.connect(self._recall_order)
        button_layout.addWidget(self.recall_btn)

        # Back button with icon
        self.back_btn = QPushButton("← Back to Tables")
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setMinimumHeight(50)
        self.back_btn.clicked.connect(self.back_requested.emit)
        button_layout.addWidget(self.back_btn)

        right_layout.addLayout(button_layout)

        main_layout.addWidget(right_panel)

        # Load categories and initial menu
        self._load_categories()

        # Install event filter for keyboard shortcuts
        self.tab_widget.installEventFilter(self)
        self.menu_scroll.installEventFilter(self)
        self.items_scroll.installEventFilter(self)

    def _hold_order(self):
        """Hold the current order."""
        if self._order is None:
            QMessageBox.warning(self, "Warning", "No order to hold")
            return
        order_service.set_order_status(self._order.id, OrderStatus.HELD)
        self._order = None
        self.back_requested.emit()

    def _recall_order(self):
        """Recall a held order (simplified: recall the most recent held order)."""
        # For simplicity, we recall the most recent held order
        # In a full implementation, we would show a list of held orders to choose from
        with session_scope() as session:
            held_orders = session.query(Order).filter(Order.status == OrderStatus.HELD).order_by(Order.id.desc()).all()
            if not held_orders:
                QMessageBox.information(self, "Info", "No held orders to recall")
                return
            # Take the most recent held order
            order = held_orders[0]
            self._order = order
            self._refresh_order_display()
        # After recall, we stay on the order screen

    def _load_or_create_order(self):
        """Load existing active order or create new one."""
        try:
            if self.order_type == OrderType.DINE_IN and self.table_id:
                self._order = order_service.get_active_for_table(self.table_id)

            if not self._order:
                self._order = order_service.create_order(
                    actor=self.current_user,
                    order_type=self.order_type,
                    table_id=self.table_id,
                    guest_count=self.guest_count
                )

            if self._order:
                self._refresh_order_display()

        except OrderError as e:
            QMessageBox.critical(self, "Error", str(e))
            self.back_requested.emit()

    def _load_categories(self):
        categories = menu_service.get_categories()
        for cat in categories:
            # Create tab content
            tab_content = QWidget()
            tab_layout = QVBoxLayout(tab_content)
            tab_layout.setContentsMargins(0, 0, 0, 0)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setSpacing(12)
            grid.setContentsMargins(8, 8, 8, 8)

            scroll.setWidget(grid_widget)
            tab_layout.addWidget(scroll)

            self.tab_widget.addTab(tab_content, cat.name)
            self._category_grids[cat.id] = grid
            self._category_scrolls[cat.id] = scroll

    def _on_category_changed(self, index: int):
        self._load_menu_for_category(index)

    def _load_menu_for_category(self, category_index: int):
        if category_index < 0:
            return

        categories = menu_service.get_categories()
        if category_index >= len(categories):
            return

        category = categories[category_index]
        self._current_category = category

        # Clear existing tiles
        for tile in self._menu_tiles:
            tile.setParent(None)
            tile.deleteLater()
        self._menu_tiles.clear()

        # Load items
        items = menu_service.get_items_by_category(category.id)

        # Populate grid (3 columns)
        cols = 3
        for i, item in enumerate(items):
            row = i // cols
            col = i % cols

            tile = MenuTile(item)
            tile.clicked.connect(self._on_menu_item_clicked)
            grid = self._category_grids.get(category.id)
            if grid is not None:
                grid.addWidget(tile, row, col)
            self._menu_tiles.append(tile)

        # Scroll to top
        scroll = self._category_scrolls.get(category.id)
        if scroll:
            scroll.verticalScrollBar().setValue(0)

    def _on_menu_item_clicked(self, menu_item: MenuItem):
        """Handle menu item selection - show modifiers if any, then add to order."""
        modifiers = menu_service.get_modifiers(menu_item.id)

        if modifiers:
            self._show_modifier_dialog(menu_item, modifiers)
        else:
            self._add_item_to_order(menu_item, [])

    def _show_modifier_dialog(self, menu_item: MenuItem, modifiers: List[Modifier]):
        """Show modifier selection dialog."""
        # For simplicity in MVP, auto-add all modifiers
        # In a full implementation, this would show a dialog
        self._add_item_to_order(menu_item, modifiers)

    def _add_item_to_order(self, menu_item: MenuItem, modifiers: List[Modifier]):
        """Add menu item with modifiers to the current order."""
        if not self._order:
            self._create_new_order()

        order_service.add_item_to_order(self._order, menu_item, quantity=1, modifiers=modifiers)
        # Re-fetch the eager-loaded order so UI code never touches detached relationships.
        self._order = order_service.get_order_summary(self._order.id)["order"]
        self._refresh_order_display()

    def _create_new_order(self):
        """Create a new order for the current user and table."""
        self._order = order_service.create_order(
            actor=self.current_user,
            order_type=self.order_type,
            table_id=self.table_id,
            guest_count=self.guest_count
        )

    def _refresh_order_display(self):
        """Refresh the order display with current items and totals."""
        # Clear existing items
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._order:
            self.items_layout.addWidget(QLabel("No order selected"))
            return

        # Add items
        for item in self._order.items:
            item_widget = OrderItemWidget(item, self.items_container)
            self.items_layout.addWidget(item_widget)

        # Order totals are calculated from persisted line items; Order has no cached total columns.
        summary = order_service.get_order_summary(self._order.id)
        self.subtotal_display.set_amount(summary.get("subtotal", Decimal("0.00")))
        self.tax_display.set_amount(summary.get("tax_total", Decimal("0.00")))
        self.total_display.set_amount(summary.get("total", Decimal("0.00")))

        self.items_layout.addStretch()

    def _send_to_kitchen(self):
        """Submit the persisted ticket through the order lifecycle service."""
        if not self._order or not self._order.items:
            QMessageBox.warning(self, "Warning", "No items in order")
            return
        try:
            self._order = order_service.send_to_kitchen(self.current_user, self._order.id)
        except OrderError as error:
            QMessageBox.warning(self, "Cannot send order", str(error))
            return
        self.order_sent_to_kitchen.emit(self._order)
        QMessageBox.information(self, "Sent", "Order sent to kitchen")
        self._create_new_order()

    def _go_to_checkout(self):
        """Request the bill, then route only a persisted bill-ready order to checkout."""
        if not self._order or not self._order.items:
            QMessageBox.warning(self, "Warning", "No items in order")
            return

        self._order = order_service.set_order_status(self._order.id, OrderStatus.BILL_REQUESTED)
        self.checkout_requested.emit(self._order)

    def apply_theme(self, theme_manager):
        """Apply theme colors to this screen's widgets."""
        palette = theme_manager._get_palette()
        # Update background
        self.setStyleSheet(f"""
            OrderScreen {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {palette['bg_gradient_start']}, stop:1 {palette['bg_gradient_end']});
            }}
        """)
        # Update specific widgets if needed - for now, rely on widget-level theming
        # But we can update container backgrounds
        # Find and update containers
        for widget in self.findChildren(QWidget):
            if widget.objectName() in ("LeftPanel", "RightPanel", "menu_scroll", "items_scroll", "totalsFrame"):
                widget.setStyleSheet(f"""
                    QWidget#{widget.objectName()} {{
                        background: {palette['glass_bg']};
                        border: 1px solid {palette['glass_border']};
                        border-radius: 8px;
                    }}
                """)
