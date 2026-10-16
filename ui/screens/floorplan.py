"""Operational floor-plan screen for Hearth POS."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from app.db.engine import session_scope
from app.db.models import DiningTable, TableStatus
from app.db.repositories import TableRepository


class FloorPlanScreen(QWidget):
    """Display active tables and expose the router actions for POS workflows."""

    table_selected = Signal(object)
    takeaway_requested = Signal()
    delivery_requested = Signal()
    logout_requested = Signal()
    manager_requested = Signal()
    shift_action_requested = Signal()
    back_requested = Signal()

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._table_buttons: dict[int, QPushButton] = {}
        self._setup_ui()
        self.refresh_tables()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title_column = QVBoxLayout()
        title = QLabel("Floor Plan")
        title.setProperty("heading", "true")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        title_column.addWidget(title)
        self.summary_label = QLabel("Loading tables…")
        self.summary_label.setProperty("secondary", "true")
        title_column.addWidget(self.summary_label)
        header.addLayout(title_column)
        header.addStretch()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_tables)
        header.addWidget(refresh_button)
        layout.addLayout(header)

        actions = QHBoxLayout()
        self.takeaway_button = QPushButton("New Takeaway")
        self.takeaway_button.setProperty("primary", "true")
        self.takeaway_button.clicked.connect(self.takeaway_requested.emit)
        actions.addWidget(self.takeaway_button)
        self.delivery_button = QPushButton("New Delivery")
        self.delivery_button.setProperty("primary", "true")
        self.delivery_button.clicked.connect(self.delivery_requested.emit)
        actions.addWidget(self.delivery_button)
        actions.addStretch()
        self.shift_button = QPushButton("Shift")
        self.shift_button.clicked.connect(self.shift_action_requested.emit)
        actions.addWidget(self.shift_button)
        self.manager_button = QPushButton("Manager")
        self.manager_button.clicked.connect(self.manager_requested.emit)
        actions.addWidget(self.manager_button)
        self.logout_button = QPushButton("Log out")
        self.logout_button.clicked.connect(self.logout_requested.emit)
        actions.addWidget(self.logout_button)
        layout.addLayout(actions)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table_container = QWidget()
        self.table_grid = QGridLayout(self.table_container)
        self.table_grid.setContentsMargins(4, 4, 4, 4)
        self.table_grid.setSpacing(12)
        scroll.setWidget(self.table_container)
        layout.addWidget(scroll, 1)

    def refresh_tables(self) -> None:
        """Reload active tables from the database and rebuild the table grid."""
        while self.table_grid.count():
            item = self.table_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._table_buttons.clear()

        with session_scope() as session:
            tables = TableRepository(session).get_all_active()
            snapshots = [(table.id, table.number, table.capacity, table.status) for table in tables]

        counts = {status: 0 for status in TableStatus}
        for _, _, _, status in snapshots:
            counts[status] += 1
        self.summary_label.setText(
            f"{len(snapshots)} tables · {counts[TableStatus.OPEN]} available · "
            f"{len(snapshots) - counts[TableStatus.OPEN]} in service"
        )

        for index, (table_id, number, capacity, status) in enumerate(snapshots):
            button = QPushButton(
                f"Table {number}\n{capacity} seats\n{status.value.replace('_', ' ').title()}"
            )
            button.setObjectName(f"table-{table_id}")
            button.setMinimumSize(160, 112)
            button.setProperty("tableStatus", status.value)
            button.clicked.connect(lambda _checked=False, id_=table_id: self._select_table(id_))
            self.table_grid.addWidget(button, index // 4, index % 4)
            self._table_buttons[table_id] = button

        if not snapshots:
            empty = QLabel("No active tables. Add tables from the manager area.")
            empty.setAlignment(Qt.AlignCenter)
            self.table_grid.addWidget(empty, 0, 0, 1, 4)

    def _select_table(self, table_id: int) -> None:
        """Fetch a current table record before emitting it to the application router."""
        with session_scope() as session:
            table = TableRepository(session).get_by_id(table_id)
            if table is None or table.is_deleted:
                return
            snapshot = DiningTable(
                id=table.id,
                number=table.number,
                capacity=table.capacity,
                status=table.status,
                is_deleted=table.is_deleted,
            )
        self.table_selected.emit(snapshot)

    def apply_theme(self, theme_manager) -> None:
        palette = theme_manager._get_palette()
        self.setStyleSheet(
            "FloorPlanScreen {"
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {palette['bg_gradient_start']}, stop:1 {palette['bg_gradient_end']});"
            "}"
        )
