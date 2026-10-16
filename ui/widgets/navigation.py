"""Hearth POS - Top navigation bar widget."""
from __future__ import annotations

from typing import Optional
from PySide6.QtCore import Qt, Signal, QTime, QTimer
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtGui import QFont

from app.db.models import StaffUser
from app.ui.theme import apply_theme


class AppTopBar(QFrame):
    """Global navigation top bar for Hearth POS."""

    logout_requested = Signal()
    kitchen_requested = Signal()
    manager_requested = Signal()
    theme_toggled = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user: Optional[StaffUser] = None
        self.current_theme: str = "dark"
        self.setObjectName("AppTopBar")
        self._setup_ui()
        self._start_clock()

    def _setup_ui(self):
        self.setFixedHeight(56)
        self.setStyleSheet("""
            QFrame#AppTopBar {
                background-color: @surface;
                border-bottom: 1px solid @border;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        # Brand / Venue Logo
        self.brand_label = QLabel("🔥 HEARTH POS")
        self.brand_label.setStyleSheet("font-size: 18px; font-weight: 800; color: @accent; letter-spacing: 2px;")
        layout.addWidget(self.brand_label)

        # Divider
        div1 = QFrame()
        div1.setFrameShape(QFrame.VLine)
        div1.setFixedHeight(24)
        div1.setStyleSheet("background-color: @border; border: none;")
        layout.addWidget(div1)

        # Active Screen / Context Title
        self.screen_title = QLabel("Login")
        self.screen_title.setStyleSheet("font-size: 15px; font-weight: 600; color: @text_primary;")
        layout.addWidget(self.screen_title)

        layout.addStretch()

        # Live Clock
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("font-size: 14px; font-weight: 500; color: @text_secondary; font-variant-numeric: tabular-nums;")
        layout.addWidget(self.clock_label)

        # Divider
        div2 = QFrame()
        div2.setFrameShape(QFrame.VLine)
        div2.setFixedHeight(24)
        div2.setStyleSheet("background-color: @border; border: none;")
        layout.addWidget(div2)

        # Active User Info
        self.user_frame = QFrame()
        self.user_frame.setVisible(False)
        user_layout = QHBoxLayout(self.user_frame)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(8)

        self.user_avatar = QLabel("U")
        self.user_avatar.setFixedSize(30, 30)
        self.user_avatar.setAlignment(Qt.AlignCenter)
        self.user_avatar.setStyleSheet("background-color: @accent; color: white; border-radius: 15px; font-weight: bold; font-size: 13px;")
        user_layout.addWidget(self.user_avatar)

        self.user_name_label = QLabel("")
        self.user_name_label.setStyleSheet("font-size: 14px; font-weight: 600; color: @text_primary;")
        user_layout.addWidget(self.user_name_label)

        self.role_badge = QLabel("")
        self.role_badge.setStyleSheet("font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 10px; background-color: @surface_raised; color: @accent;")
        user_layout.addWidget(self.role_badge)

        layout.addWidget(self.user_frame)

        # Quick Actions
        self.kitchen_btn = QPushButton("🍳 Kitchen")
        self.kitchen_btn.setVisible(False)
        self.kitchen_btn.setStyleSheet("padding: 6px 12px; font-size: 13px; min-height: 32px;")
        self.kitchen_btn.clicked.connect(self.kitchen_requested.emit)
        layout.addWidget(self.kitchen_btn)

        self.manager_btn = QPushButton("📊 Manager")
        self.manager_btn.setVisible(False)
        self.manager_btn.setStyleSheet("padding: 6px 12px; font-size: 13px; min-height: 32px;")
        self.manager_btn.clicked.connect(self.manager_requested.emit)
        layout.addWidget(self.manager_btn)

        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setToolTip("Toggle Dark/Light Mode")
        self.theme_btn.setStyleSheet("padding: 0px; font-size: 16px; min-height: 32px; border-radius: 18px;")
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        self.logout_btn = QPushButton("🔒 Lock")
        self.logout_btn.setVisible(False)
        self.logout_btn.setStyleSheet("padding: 6px 12px; font-size: 13px; min-height: 32px; background-color: @surface_raised; color: @err; border-color: @border;")
        self.logout_btn.clicked.connect(self.logout_requested.emit)
        layout.addWidget(self.logout_btn)

    def _start_clock(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_clock)
        self._timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        now = QTime.currentTime().toString("hh:mm:ss AP")
        self.clock_label.setText(now)

    def set_context(self, screen_title: str, user: Optional[StaffUser] = None):
        """Update top bar state according to active screen and logged-in user."""
        self.screen_title.setText(screen_title)
        self.current_user = user

        if user:
            self.user_frame.setVisible(True)
            self.logout_btn.setVisible(True)

            initials = "".join([n[0] for n in user.name.split()[:2]]).upper()
            self.user_avatar.setText(initials)
            self.user_name_label.setText(user.name)
            self.role_badge.setText(user.role.value.title())

            # Show role-appropriate quick links
            self.kitchen_btn.setVisible(user.role.value in ("manager", "kitchen", "waiter"))
            self.manager_btn.setVisible(user.role.value == "manager")
        else:
            self.user_frame.setVisible(False)
            self.kitchen_btn.setVisible(False)
            self.manager_btn.setVisible(False)
            self.logout_btn.setVisible(False)

    def _toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.theme_btn.setText("☀️" if self.current_theme == "light" else "🌙")
        self.theme_toggled.emit(self.current_theme)
