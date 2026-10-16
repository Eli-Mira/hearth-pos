"""Manager dashboard screen."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
)
from app.ui.widgets.component_library import get_palette

class ManagerDashboard(QWidget):
    """Manager dashboard screen."""

    logout_requested = Signal()

    def __init__(self, current_user=None, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Manager Dashboard")
        title.setProperty("heading", "true")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title)

        subtitle = QLabel("This is a simplified manager dashboard.")
        subtitle.setProperty("secondary", "true")
        subtitle.setStyleSheet("font-size: 14px;")
        main_layout.addWidget(subtitle)

        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setProperty("primary", "true")
        self.logout_btn.clicked.connect(self.logout_requested.emit)
        main_layout.addWidget(self.logout_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def apply_theme(self, theme_manager):
        """Apply theme colors."""
        palette = theme_manager._get_palette()
        self.setStyleSheet(f"""
            ManagerDashboard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {{palette['bg_gradient_start']}}, stop:1 {{palette['bg_gradient_end']}});
            }}
        """.format(palette=palette))
