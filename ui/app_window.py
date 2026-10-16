"""Hearth POS - Main window and screen router with theme management."""
from __future__ import annotations

from typing import Optional
from functools import partial

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QMessageBox, QStackedWidget, QGraphicsOpacityEffect, QApplication

from app.ui.theme import ThemeManager
from app.ui.screens.login import LoginScreen
from app.ui.screens.floorplan import FloorPlanScreen
from app.ui.screens.order import OrderScreen
from app.ui.screens.checkout import CheckoutScreen
from app.ui.screens.kitchen import KitchenScreen
from app.ui.screens.manager import ManagerDashboard
from app.ui.widgets.navigation import AppTopBar
from app.db.models import StaffUser, DiningTable, Order, OrderType
from app.services.auth import auth_service


class AppWindow(QMainWindow):
    """Main application window managing screen transitions and theme."""

    def __init__(self):
        super().__init__()
        self.current_user: Optional[StaffUser] = None
        self.theme_manager = ThemeManager.instance()
        self._setup_ui()
        self._connect_theme_signals()
        self.show_login()

    def _setup_ui(self):
        self.setWindowTitle("Hearth POS")
        self.setMinimumSize(1024, 768)
        self.resize(1400, 900)

        # Create central container widget
        central_container = QWidget()
        self.setCentralWidget(central_container)
        
        # Main vertical layout
        main_layout = QVBoxLayout(central_container)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top navigation bar
        self.top_bar = AppTopBar()
        self.top_bar.logout_requested.connect(self.show_login)
        self.top_bar.kitchen_requested.connect(self.show_kitchen)
        self.top_bar.manager_requested.connect(self.show_manager)
        self.top_bar.theme_toggled.connect(self._on_theme_toggled)
        main_layout.addWidget(self.top_bar)

        # Central stack for screen switching
        self.central_stack = QStackedWidget()
        self.central_stack.setObjectName("AppCentral")
        main_layout.addWidget(self.central_stack, 1)  # Take all remaining space

        # Apply initial theme
        self._apply_theme_to_ui()

    def _connect_theme_signals(self):
        """Connect theme manager signals to UI updates."""
        self.theme_manager.themeChanged.connect(self._on_theme_changed)

    def _on_theme_changed(self, is_dark: bool):
        """Called when theme manager toggles theme."""
        print(f"Theme changed: {'dark' if is_dark else 'light'}")
        self._apply_theme_to_ui()

    def _apply_theme_to_ui(self):
        """Apply current theme to all widgets."""
        theme = self.theme_manager
        palette = theme._get_palette()
        app = QApplication.instance()
        if app:
            # Apply global stylesheet
            app.setStyleSheet(self._generate_global_stylesheet(palette))
        
        # Re-apply to screens
        for i in range(self.central_stack.count()):
            screen = self.central_stack.widget(i)
            if hasattr(screen, 'apply_theme'):
                screen.apply_theme(theme)

    def _generate_global_stylesheet(self, palette):
        """Generate QSS stylesheet from palette."""
        return f"""
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {palette['bg_gradient_start']}, stop:1 {palette['bg_gradient_end']});
            color: {palette['text_primary']};
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 10pt;
        }}

        QLineEdit, QTextEdit, QComboBox {{
            background: {palette['glass_bg']};
            border: 1px solid {palette['glass_border']};
            border-radius: 4px;
            padding: 6px;
            color: {palette['text_primary']};
        }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border: 1px solid {palette['accent']};
        }}
        """

    def _clear_stack(self):
        """Remove and delete all widgets in the stack."""
        while self.central_stack.count():
            widget = self.central_stack.widget(0)
            self.central_stack.removeWidget(widget)
            widget.deleteLater()

    def show_login(self):
        """Show the login screen."""
        self._clear_stack()
        self.current_user = None
        self.top_bar.set_context("Login", None)
        
        login_screen = LoginScreen()
        login_screen.login_successful.connect(self._on_pin_entered)
        login_screen.back_requested.connect(self._on_login_back)
        self.central_stack.addWidget(login_screen)
        self.central_stack.setCurrentWidget(login_screen)

    def _on_login_back(self):
        """Handle back button on login screen - close app."""
        self.close()

    def _on_pin_entered(self, pin: str):
        """Handle PIN entry from login screen."""
        user = auth_service.authenticate(pin)
        if user:
            self._on_login_success(user)
        else:
            # Get the login screen and show error
            login_screen = self.central_stack.currentWidget()
            if hasattr(login_screen, 'show_error'):
                login_screen.show_error("Invalid PIN. Please try again.")

    def _on_login_success(self, user: StaffUser):
        """Handle successful login."""
        self.current_user = user
        self.show_floorplan()

    def show_floorplan(self):
        """Show the table / floor plan view."""
        self._clear_stack()
        self.top_bar.set_context("Floor Plan", self.current_user)
        
        floorplan = FloorPlanScreen(self.current_user)
        floorplan.table_selected.connect(self._on_table_selected)
        floorplan.takeaway_requested.connect(lambda: self.show_order(OrderType.TAKEAWAY))
        floorplan.delivery_requested.connect(lambda: self.show_order(OrderType.DELIVERY))
        floorplan.logout_requested.connect(self.show_login)
        floorplan.manager_requested.connect(self.show_manager)
        floorplan.shift_action_requested.connect(self._on_shift_action)
        
        self.central_stack.addWidget(floorplan)
        self.central_stack.setCurrentWidget(floorplan)

    def show_order(self, order_type: OrderType, table_id: Optional[int] = None):
        """Show the order entry screen."""
        self._clear_stack()
        
        # Update top bar context
        if order_type == OrderType.DINE_IN and table_id:
            self.top_bar.set_context("Order", self.current_user)
        else:
            self.top_bar.set_context(f"{order_type.value.title()} Order", self.current_user)
        
        order_screen = OrderScreen(self.current_user, order_type, table_id)
        order_screen.back_requested.connect(self.show_floorplan)
        order_screen.checkout_requested.connect(self.show_checkout)
        
        self.central_stack.addWidget(order_screen)
        self.central_stack.setCurrentWidget(order_screen)

    def show_checkout(self, order: Order):
        """Show the checkout / payment screen."""
        self._clear_stack()
        self.top_bar.set_context("Checkout", self.current_user)
        
        checkout_screen = CheckoutScreen(self.current_user, order)
        checkout_screen.back_requested.connect(lambda: self.show_order(order.order_type, order.table_id))
        checkout_screen.payment_completed.connect(self._on_payment_complete)
        
        self.central_stack.addWidget(checkout_screen)
        self.central_stack.setCurrentWidget(checkout_screen)

    def show_manager(self):
        """Show the manager dashboard."""
        self._clear_stack()
        self.top_bar.set_context("Manager", self.current_user)
        
        manager = ManagerDashboard(self.current_user)
        manager.logout_requested.connect(self.show_login)
        
        self.central_stack.addWidget(manager)
        self.central_stack.setCurrentWidget(manager)

    def show_kitchen(self):
        """Show the kitchen display screen."""
        self._clear_stack()
        self.top_bar.set_context("Kitchen", self.current_user)
        
        kitchen = KitchenScreen(self.current_user)
        kitchen.back_requested.connect(self.show_floorplan)
        
        self.central_stack.addWidget(kitchen)
        self.central_stack.setCurrentWidget(kitchen)

    def _on_theme_toggled(self, theme: str):
        """Handle theme toggle from top bar."""
        print(f"Toggling to theme: {theme}")
        self.theme_manager.toggle_theme()

    def _on_table_selected(self, table: DiningTable):
        """Handle table selection from floor plan."""
        self.top_bar.set_context(f"Table {table.number}", self.current_user)
        self.show_order(OrderType.DINE_IN, table.id)

    def _on_payment_complete(self, order: Order):
        """Handle completed payment."""
        QMessageBox.information(self, "Success", f"Order {order.id} paid successfully.")
        self.show_floorplan()

    def _on_shift_action(self):
        """Open the management area where staff can open, close, and reconcile a shift."""
        self.show_manager()