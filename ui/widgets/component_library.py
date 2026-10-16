"""Hearth POS - Base UI component library with themed widgets."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, Slot, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPalette, QBrush, QIcon
from PySide6.QtWidgets import (
    QWidget, QFrame, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QScrollBar, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QSizePolicy
)


# =============================================================================
# Theme Integration - Dynamic Palette Access
# =============================================================================
from app.ui.theme import ThemeManager

def get_palette():
    """Get the current theme palette from the singleton ThemeManager."""
    return ThemeManager.instance()._get_palette()


# =============================================================================
# BaseTile - Glassmorphic Container
# =============================================================================
class BaseTile(QFrame):
    """Base class for clickable tiles with glassmorphism."""
    
    clicked = Signal()
    
    def __init__(self, label="", icon=None, parent=None):
        super().__init__(parent)
        self._label = label
        self._icon = icon
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup tile appearance."""
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            BaseTile {{
                background: {get_palette()['glass_bg']};
                border: 1px solid {get_palette()['glass_border']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        # Visual feedback
        self.setStyleSheet(f"""
            BaseTile {{
                background: {get_palette()['glass_bg']};
                border: 2px solid {ThemeVars.accent()};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        # Restore normal style
        self.setStyleSheet(f"""
            BaseTile {{
                background: {get_palette()['glass_bg']};
                border: 1px solid {get_palette()['glass_border']};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        super().mouseReleaseEvent(event)


# =============================================================================
# StatefulButton - Themed Button with States
# =============================================================================
class StatefulButton(QPushButton):
    """Button with visual state management (enabled/pressed/hover)."""
    
    def __init__(self, label="", parent=None):
        super().__init__(label, parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup button appearance."""
        self.setStyleSheet(f"""
            StatefulButton {{
                background-color: {ThemeVars.accent()};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10pt;
            }}
            StatefulButton:hover {{
                background-color: {ThemeVars.accent() + "33"};
            }}
            StatefulButton:pressed {{
                background-color: {ThemeVars.accent() + "66"};
            }}
        """)
    
    def set_disabled(self, disabled):
        """Set visual disabled state."""
        if disabled:
            self.setStyleSheet(f"""
                StatefulButton {{
                    background-color: {get_palette()['text_secondary']};
                    color: {get_palette()['bg_gradient_start']};
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 10pt;
                }}
            """)
        else:
            self._setup_ui()


# =============================================================================
# Badge - Themed Status Indicator
# =============================================================================
class Badge(QFrame):
    """Compact status badge with theme-aware colors."""
    
    def __init__(self, text="", color=None, parent=None):
        super().__init__(parent)
        self._text = text
        self._color = color or "default"
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup badge appearance."""
        color_map = {
            "default": f"background: {get_palette()['accent']}; color: white;",
            "warning": f"background: #FF9800; color: white;",
            "error": f"background: #F44336; color: white;",
            "success": f"background: #4CAF50; color: white;",
            "info": f"background: {ThemeVars.accent()}; color: white;",
        }
        
        self.setStyleSheet(f"""
            Badge {{
                {color_map.get(self._color, color_map["default"])};
                border-radius: 4px;
                padding: 2px 8px;
            }}
        """)
        self.setMaximumWidth(60)


# =============================================================================
# ProgressBar - Themed Progress Indicator
# =============================================================================
class ProgressBar(QFrame):
    """Custom progress bar with glassmorphism."""
    
    def __init__(self, value=0, parent=None):
        super().__init__(parent)
        self._value = value
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup progress bar appearance."""
        self.setMaximumHeight(8)
        self.setStyleSheet(f"""
            ProgressBar {{
                background: {get_palette()['glass_bg']};
                border: 1px solid {get_palette()['glass_border']};
                border-radius: 4px;
            }}
            ProgressBar QWidget {{
                background: {ThemeVars.accent()};
                border-radius: 3px;
            }}
        """)
    
    def set_value(self, value):
        """Set progress value (0-100)."""
        self._value = max(0, min(100, value))
        # Repaint or trigger update
        self.update()


# =============================================================================
# Card - Themed Container with Shadow
# =============================================================================
class Card(QFrame):
    """Card with glassmorphism and subtle shadow."""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self._title = title
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup card appearance."""
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        # Apply shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        self.setStyleSheet(f"""
            Card {{
                background: {get_palette()['glass_bg']};
                border: 1px solid {get_palette()['glass_border']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)


# =============================================================================
# QuickAction - Icon Button with Label
# =============================================================================
class QuickAction(QPushButton):
    """Button with icon and description for quick actions."""
    
    def __init__(self, icon_name, description="", parent=None):
        super().__init__(parent)
        self._icon = QIcon(icon_name) if icon_name else None
        self._description = description
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup quick action button."""
        layout = QVBoxLayout(self)
        
        if self._icon:
            self._icon_label = QLabel()
            self._icon_label.setPixmap(self._icon.pixmap(32, 32))
            layout.addWidget(self._icon_label)
        
        self._desc_label = QLabel(self._description)
        self._desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._desc_label)
        
        layout.addStretch()
        self.setStyleSheet(f"""
            QuickAction {{
                background: transparent;
                border: none;
                padding: 8px;
            }}
            QuickAction QLabel {{
                color: {get_palette()['text_secondary']};
            }}
        """)


# =============================================================================
# DataTable - Glassmorphic Table with Themed Selection
# =============================================================================
class DataTable(QTableWidget):
    """Data table with glassmorphism styling."""
    
    def __init__(self, rows=0, columns=0, parent=None):
        super().__init__(rows, columns, parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup table appearance."""
        self.setStyleSheet(f"""
            DataTable {{
                background: {get_palette()['glass_bg']};
                gridline-color: {get_palette()['glass_border']};
                border: 1px solid {get_palette()['glass_border']};
                border-radius: 6px;
            }}
            DataTable::item {{
                padding: 4px;
                color: {get_palette()['text_primary']};
            }}
            DataTable::item:selected {{
                background: {ThemeVars.accent()} + "22";
                color: {ThemeVars.accent()};
            }}
            DataTable QHeaderView::section {{
                background: {get_palette()['glass_bg']};
                color: {get_palette()['text_primary']};
                padding: 4px;
                border: 1px solid {get_palette()['glass_border']};
            }}
        """)


# =============================================================================
# Theme Toggle Button - With Animation
# =============================================================================
class ThemeToggleButton(QPushButton):
    """Animated theme toggle button (Sun/Moon)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup toggle button."""
        self.setCheckable(True)
        self.setStyleSheet(f"""
            ThemeToggleButton {{
                background: {get_palette()['glass_bg']};
                border: 1px solid {get_palette()['glass_border']};
                border-radius: 20px;
                padding: 8px 12px;
                font-size: 12pt;
            }}
            ThemeToggleButton:checked {{
                background: {get_palette()['glass_bg']};
            }}
        """)
        self.setToolTip("Toggle theme (Light/Dark)")
    
    def toggle(self):
        """Toggle theme with animation."""
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(200)
        anim.setStartValue(1.0)
        anim.setEndValue(0.8)
        anim.start()
        
        super().toggle()
        anim.setStartValue(0.8)
        anim.setEndValue(1.0)
        anim.start()


# =============================================================================
# Fade Animation Helper
# =============================================================================
def fade_animation(widget, duration=200):
    """Apply fade animation to widget."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(1.0)
    anim.setEndValue(0.0)
    anim.start()
    
    return effect, anim