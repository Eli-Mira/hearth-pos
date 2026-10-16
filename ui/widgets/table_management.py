"""Table Management Dialog - enhanced table management for restaurant staff."""
from __future__ import annotations

from typing import Dict, Optional, List
from decimal import Decimal

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QFrame, QSizePolicy, QMessageBox, QInputDialog, QListWidget,
    QDialogButtonBox, QScrollArea, QWidget
)
from PySide6.QtGui import QFont

from app.db.models import DiningTable, TableStatus, Order, OrderStatus
from app.services.orders import order_service
from app.services.shifts import shift_service


class CombineSelectionDialog(QDialog):
    """Dialog to select tables to combine."""

    def __init__(self, tables: List[DiningTable], parent=None):
        super().__init__(parent)
        self.tables = tables
        self.selected_table_ids: List[int] = []
        self.setWindowTitle("Select Tables to Combine")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        label = QLabel("Select exactly two tables to combine:")
        label.setStyleSheet("font-weight: 600; color: @text-primary;")
        layout.addWidget(label)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: @input_bg;
                border: 1px solid @border;
                border-radius: 8px;
                color: @text-primary;
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: @accent;
                color: white;
            }
        """)

        for table in self.tables:
            self.list_widget.addItem(f"Table {table.number} - {table.name} ({table.status.value.replace('_', ' ').title()})")

        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept(self):
        selected_items = self.list_widget.selectedItems()
        if len(selected_items) != 2:
            QMessageBox.warning(self, "Invalid Selection", "Please select exactly two tables to combine.")
            return

        # Map selected item text back to table IDs
        self.selected_table_ids = []
        for item in selected_items:
            idx = self.list_widget.row(item)
            self.selected_table_ids.append(self.tables[idx].id)

        self.accept()


class TableManagementDialog(QDialog):
    """Enhanced table management dialog for managing dining tables."""

    def __init__(self, table_cells: Dict[int, QFrame], parent=None):
        super().__init__(parent)
        self.table_cells = table_cells
        self._table_widgets = {}
        self._setup_ui()
        self._load_tables()
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.setWindowTitle("Table Management")

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Manage Tables")
        header.setProperty("heading", "true")
        header.setStyleSheet("font-size: 20px; color: @text-primary;")
        main_layout.addWidget(header)

        # Table status controls
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        status_layout.setSpacing(12)

        status_label = QLabel("Show:")
        status_label.setStyleSheet("color: @text-secondary; font-size: 14px;")
        status_layout.addWidget(status_label)

        self.status_combo = QComboBox()
        self.status_combo.addItem("All Tables", "all")
        self.status_combo.addItem("Available", "open")
        self.status_combo.addItem("Occupied", "occupied")
        self.status_combo.addItem("Needs Attention", "attention")
        self.status_combo.currentIndexChanged.connect(self._filter_tables)
        status_layout.addWidget(self.status_combo)

        status_layout.addStretch()
        main_layout.addWidget(status_frame)

        # Table grid inside a scroll area for responsiveness
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        grid_widget = QWidget()
        self.table_grid = QGridLayout(grid_widget)
        self.table_grid.setSpacing(16)
        self.table_grid.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(grid_widget)
        main_layout.addWidget(scroll, 1)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        button_layout.addStretch()

        self.combine_btn = QPushButton("🔗 Combine Tables")
        self.combine_btn.setMinimumHeight(50)
        self.combine_btn.clicked.connect(self._combine_tables)
        button_layout.addWidget(self.combine_btn)

        self.split_btn = QPushButton("➕ Split Table")
        self.split_btn.setMinimumHeight(50)
        self.split_btn.clicked.connect(self._split_table)
        button_layout.addWidget(self.split_btn)

        self.close_btn = QPushButton("✕ Close")
        self.close_btn.setMinimumHeight(50)
        self.close_btn.setProperty("danger", "true")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        main_layout.addLayout(button_layout)

    def _load_tables(self):
        """Load and display all tables."""
        # Clear existing
        for widget in self._table_widgets.values():
            widget.setParent(None)
            widget.deleteLater()
        self._table_widgets.clear()

        from app.db.engine import session_scope
        from app.db.repositories import TableRepository

        with session_scope() as session:
            tables = TableRepository(session).get_all_active()

        # Arrange in grid (4 columns)
        cols = 4
        for i, table in enumerate(tables):
            row = i // cols
            col = i % cols

            widget = self._create_table_widget(table)
            self._table_widgets[table.id] = widget
            self.table_grid.addWidget(widget, row, col)

    def _create_table_widget(self, table: DiningTable) -> QFrame:
        """Create a table management widget."""
        widget = QFrame()
        widget.setObjectName("tableMgmtWidget")
        widget.setStyleSheet("""
            QFrame#tableMgmtWidget {
                background-color: @surface;
                border: 2px solid @border;
                border-radius: 14px;
                padding: 16px;
            }
            QFrame#tableMgmtWidget:hover {
                border-color: @accent;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Table identifier
        header = QHBoxLayout()
        table_num = QLabel(f"Table {table.number}")
        table_num.setProperty("heading", "true")
        table_num.setStyleSheet("font-size: 18px;")
        header.addWidget(table_num)

        # Current status badge
        status_badge = QLabel(table.status.value.replace("_", " ").title())
        status_badge.setAlignment(Qt.AlignCenter)
        status_badge.setProperty("status", "true")
        header.addWidget(status_badge)

        layout.addLayout(header)

        # Details
        details = QVBoxLayout()
        details.setSpacing(4)

        name_label = QLabel(table.name)
        name_label.setStyleSheet("color: @text-primary; font-size: 14px;")
        details.addWidget(name_label)

        capacity_label = QLabel(f"Capacity: {table.capacity}")
        capacity_label.setStyleSheet("color: @text-secondary; font-size: 12px;")
        details.addWidget(capacity_label)

        # Current order info
        order_info = self._get_table_order_info(table.id)
        if order_info:
            order_label = QLabel(order_info)
            order_label.setStyleSheet("color: @accent; font-size: 12px; font-weight: 600;")
            details.addWidget(order_label)

        layout.addLayout(details)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(8)

        # Modify status
        modify_btn = QPushButton("Modify")
        modify_btn.setFixedSize(80, 36)
        modify_btn.clicked.connect(lambda t=table: self._modify_table_status(t))
        actions.addWidget(modify_btn)

        # Clear order
        clear_btn = QPushButton("Clear Order")
        clear_btn.setFixedSize(100, 36)
        clear_btn.clicked.connect(lambda t=table: self._clear_order(t))
        actions.addWidget(clear_btn)

        layout.addLayout(actions)

        return widget

    def _get_table_order_info(self, table_id: int) -> str:
        """Get order information for a table."""
        from app.db.engine import session_scope
        from app.db.repositories import OrderRepository

        with session_scope() as session:
            order = OrderRepository(session).get_active_for_table(table_id)
            if order:
                item_count = len([i for i in order.items if not i.voided])
                return f"{item_count} items | ${order.total:.2f}"
        return ""

    def _filter_tables(self, index: int):
        """Filter tables by status."""
        filter_type = self.status_combo.itemData(index)

        for table_id, widget in self._table_widgets.items():
            if filter_type == "all":
                widget.show()
            elif filter_type == "open":
                status_label = widget.findChild(QLabel)
                if status_label and "Available" in status_label.text():
                    widget.show()
                else:
                    widget.hide()
            elif filter_type == "occupied":
                status_label = widget.findChild(QLabel)
                if status_label and "Seated" in status_label.text():
                    widget.show()
                else:
                    widget.hide()
            elif filter_type == "attention":
                status_label = widget.findChild(QLabel)
                if status_label and ("Ordered" in status_label.text() or "Bill" in status_label.text()):
                    widget.show()
                else:
                    widget.hide()

    def _modify_table_status(self, table: DiningTable):
        """Modify a table's status."""
        status, ok = QInputDialog.getItem(
            self,
            "Change Status",
            "Select new status:",
            [s.value for s in TableStatus],
            current_index=TableStatus.OPEN.value,
            editable=False
        )
        if ok and status != table.status.value:
            from app.db.engine import session_scope
            from app.db.repositories import TableRepository

            with session_scope() as session:
                TableRepository(session).update_status(table.id, TableStatus[status])
            self._load_tables()

    def _clear_order(self, table: DiningTable):
        """Clear a table's order (force void all items)."""
        reply = QMessageBox.question(
            self,
            "Clear Order",
            f"Clear all items for {table.name}? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            from app.db.engine import session_scope
            from app.db.repositories import OrderRepository, OrderItemRepository

            with session_scope() as session:
                order = OrderRepository(session).get_active_for_table(table.id)
                if order:
                    item_repo = OrderItemRepository(session)
                    for item in order.items:
                        if not item.voided:
                            item_repo.void_item(item.id, "Table cleared by manager", manager_override=True)
                    # Update order status
                    order_service.request_bill(
                        order.opened_by_user.user,
                        order.id
                    )
            self._load_tables()

    def _combine_tables(self):
        """Combine two tables."""
        from app.db.engine import session_scope
        from app.db.repositories import TableRepository

        with session_scope() as session:
            tables = TableRepository(session).get_all_active()

        dialog = CombineSelectionDialog(tables, self)
        if dialog.exec() == QDialog.Accepted:
            table_id_1, table_id_2 = dialog.selected_table_ids
            
            with session_scope() as session:
                table_repo = TableRepository(session)
                t1 = table_repo.get_by_id(table_id_1)
                t2 = table_repo.get_by_id(table_id_2)
                
                # Combine capacities
                new_capacity = t1.capacity + t2.capacity
                table_repo.update_capacity(t1.id, new_capacity)
                
                # Update status of t2 to Combined
                table_repo.update_status(t2.id, TableStatus.SEATED) # Set occupied
                
                QMessageBox.information(
                    self, "Success",
                    f"Combined Table {t1.number} and Table {t2.number}.\nNew Capacity for Table {t1.number} is {new_capacity}."
                )
            
            self._load_tables()

    def _split_table(self):
        """Split a table."""
        from app.db.engine import session_scope
        from app.db.repositories import TableRepository

        with session_scope() as session:
            tables = [t for t in TableRepository(session).get_all_active() if t.capacity > 4]

        if not tables:
            QMessageBox.warning(self, "Split Table", "No combined or large tables available to split.")
            return

        table_names = [f"Table {t.number} - {t.name} (Capacity: {t.capacity})" for t in tables]
        choice, ok = QInputDialog.getItem(
            self, "Split Table", "Select table to split:",
            table_names, editable=False
        )

        if ok:
            idx = table_names.index(choice)
            target_table = tables[idx]
            
            with session_scope() as session:
                table_repo = TableRepository(session)
                # Reduce capacity by 2
                new_capacity = max(2, target_table.capacity - 2)
                table_repo.update_capacity(target_table.id, new_capacity)
                
                QMessageBox.information(
                    self, "Success",
                    f"Split Table {target_table.number}.\nNew Capacity is {new_capacity}."
                )
            
            self._load_tables()
