"""Login screen - Hearth POS."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
)
from app.ui.widgets.component_library import get_palette
from app.ui.widgets.navigation import AppTopBar
from app.ui.widgets import PinPadWidget


class LoginScreen(QWidget):
    """Login screen with PIN pad entry."""

    login_successful = Signal(object)  # Emits StaffUser
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(32, 32, 32, 32)

        # Title
        title = QLabel("Hearth POS")
        title.setProperty("heading", "true")
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Enter your PIN to continue")
        subtitle.setProperty("secondary", "true")
        subtitle.setStyleSheet("font-size: 16px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        # PIN pad widget
        self.pin_pad = PinPadWidget()
        self.pin_pad.pin_entered.connect(self._on_pin_entered)
        self.pin_pad.pin_cleared.connect(self._on_pin_cleared)
        main_layout.addWidget(self.pin_pad, alignment=Qt.AlignmentFlag.AlignCenter)

        # Error label (hidden by default)
        self.error_label = QLabel("")
        self.error_label.setProperty("error", "true")
        self.error_label.setStyleSheet("color: @err; font-size: 14px;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setVisible(False)
        main_layout.addWidget(self.error_label)

        # Back button
        self.back_btn = QPushButton("Back")
        self.back_btn.setProperty("secondary", "true")
        self.back_btn.clicked.connect(self.back_requested.emit)
        main_layout.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _on_pin_entered(self, pin: str):
        """Handle PIN entry - emit signal for authentication."""
        # Clear error
        self.error_label.setVisible(False)
        # PIN will be validated by the app window
        self.login_successful.emit(pin)

    def _on_pin_cleared(self):
        """Handle PIN cleared - hide error."""
        self.error_label.setVisible(False)

    def show_error(self, message: str):
        """Show error message."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        self.pin_pad.clear()

    def clear(self):
        """Clear the PIN pad and error."""
        self.pin_pad.clear()
        self.error_label.setVisible(False)

    def apply_theme(self, theme_manager):
        """Apply theme colors."""
        palette = theme_manager._get_palette()
        self.setStyleSheet(f"""
            LoginScreen {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {palette['bg_gradient_start']}, stop:1 {palette['bg_gradient_end']});
            }}
        """)