# ThemeManager - app/ui/theme.py
"""
Centralized theme management for Hearth POS.
Provides Light/Dark mode color variables and dynamic QSS stylesheet generation.
"""

from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication


class ThemeManager(QObject):
    """Singleton-like theme manager for Hearth POS."""

    _instance = None

    def __init__(self, parent=None):
        super().__init__(parent)
        if ThemeManager._instance is not None:
            raise RuntimeError("Use ThemeManager.instance() to get the singleton")
        ThemeManager._instance = self

        # Default to light mode
        self._dark_mode = False
        self._apply_theme()

    @staticmethod
    def instance():
        """Get the singleton instance."""
        if ThemeManager._instance is None:
            ThemeManager._instance = ThemeManager()  # Create singleton
        return ThemeManager._instance

    # ----- Color Palettes -----
    # Light Mode (Frosted Cyan Glassmorphism)
    LIGHT_BG_GRADIENT_START = "#E0F7FA"  # soft cyan
    LIGHT_BG_GRADIENT_END = "#ECEFF1"    # light cool-grey
    LIGHT_GLASS_BG = "rgba(255, 255, 255, 0.45)"  # frosted glass
    LIGHT_GLASS_BORDER = "rgba(255, 255, 255, 0.65)"
    LIGHT_TEXT_PRIMARY = "#263238"       # dark slate-grey
    LIGHT_TEXT_SECONDARY = "#546E7A"     # muted cool-grey
    LIGHT_ACCENT = "#00ACC1"             # vibrant cyan
    LIGHT_HOVER_ACCENT = "rgba(0, 172, 193, 0.15)"

    # Dark Mode (Space-Navy Glassmorphism)
    DARK_BG_GRADIENT_START = "#0A192F"   # deep space-navy
    DARK_BG_GRADIENT_END = "#172A45"     # rich dark slate
    DARK_GLASS_BG = "rgba(23, 42, 69, 0.5)"
    DARK_GLASS_BORDER = "rgba(100, 255, 218, 0.15)"
    DARK_TEXT_PRIMARY = "#F8F9FA"        # crisp off-white
    DARK_TEXT_SECONDARY = "#8892B0"      # cool grey-teal
    DARK_ACCENT = "#64FFDA"              # electric cyan/teal
    DARK_HOVER_ACCENT = "rgba(100, 255, 218, 0.1)"

    def _get_palette(self):
        """Return the current color palette as a dict."""
        if self._dark_mode:
            return {
                "bg_gradient_start": self.DARK_BG_GRADIENT_START,
                "bg_gradient_end": self.DARK_BG_GRADIENT_END,
                "glass_bg": self.DARK_GLASS_BG,
                "glass_border": self.DARK_GLASS_BORDER,
                "text_primary": self.DARK_TEXT_PRIMARY,
                "text_secondary": self.DARK_TEXT_SECONDARY,
                "accent": self.DARK_ACCENT,
                "hover_accent": self.DARK_HOVER_ACCENT,
            }
        else:
            return {
                "bg_gradient_start": self.LIGHT_BG_GRADIENT_START,
                "bg_gradient_end": self.LIGHT_BG_GRADIENT_END,
                "glass_bg": self.LIGHT_GLASS_BG,
                "glass_border": self.LIGHT_GLASS_BORDER,
                "text_primary": self.LIGHT_TEXT_PRIMARY,
                "text_secondary": self.LIGHT_TEXT_SECONDARY,
                "accent": self.LIGHT_ACCENT,
                "hover_accent": self.LIGHT_HOVER_ACCENT,
            }

    def _apply_theme(self):
        """Generate and apply the global QSS stylesheet."""
        app = QApplication.instance()
        if not app:
            return

        p = self._get_palette()
        qss = f"""
        /* Global Application Stylesheet */
        QWidget {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {p['bg_gradient_start']}, stop:1 {p['bg_gradient_end']});
            color: {p['text_primary']};
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 10pt;
        }}

        /* Glassmorphic Panels (BaseTile, Card, etc.) */
        .GlassPanel {{
            background: {p['glass_bg']};
            border: 1px solid {p['glass_border']};
            border-radius: 8px;
        }}

        /* Primary Buttons */
        QPushButton {{
            background-color: {p['accent']};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {p['hover_accent']};
        }}
        QPushButton:pressed {{
            background-color: {p['accent']};
        }}

        /* Secondary Buttons (e.g., Cancel) */
        QPushButton[flat="true"] {{
            background-color: transparent;
            color: {p['text_primary']};
            border: 1px solid {p['glass_border']};
            border-radius: 4px;
            padding: 6px 12px;
        }}
        QPushButton[flat="true"]:hover {{
            background-color: {p['hover_accent']};
        }}

        /* Input Fields */
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {p['glass_bg']};
            border: 1px solid {p['glass_border']};
            border-radius: 4px;
            padding: 6px;
            color: {p['text_primary']};
            selection-background-color: {p['accent']};
        }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border: 1px solid {p['accent']};
        }}

        /* Labels */
        QLabel {{
            color: {p['text_primary']};
        }}
        QLabel[secondary="true"] {{
            color: {p['text_secondary']};
        }}

        /* Tables */
        QTableWidget {{
            background-color: {p['glass_bg']};
            gridline-color: {p['glass_border']};
            border: 1px solid {p['glass_border']};
            border-radius: 6px;
        }}
        QTableWidget::item {{
            padding: 4px;
        }}
        QTableWidget::item:selected {{
            background-color: {p['hover_accent']};
        }}
        QHeaderView::section {{
            background-color: {p['glass_bg']};
            color: {p['text_primary']};
            padding: 4px;
            border: 1px solid {p['glass_border']};
            font-weight: bold;
        }}

        /* Scroll Bars */
        QScrollBar:vertical {{
            background: {p['glass_bg']};
            width: 12px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {p['accent']};
            min-height: 20px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {p['hover_accent']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        /* Tooltips */
        QToolTip {{
            background-color: {p['glass_bg']};
            color: {p['text_primary']};
            border: 1px solid {p['glass_border']};
            border-radius: 4px;
        }}
        """
        app.setStyleSheet(qss)

    @Slot()
    def toggle_theme(self):
        """Toggle between light and dark mode and reapply stylesheet."""
        self._dark_mode = not self._dark_mode
        self._apply_theme()
        # Emit signal if needed for other components to update
        self.themeChanged.emit(self._dark_mode)

    # ----- Signals -----
    themeChanged = Signal(bool)  # emits True for dark, False for light

    # ----- Properties -----
    @Property(bool, notify=themeChanged)
    def darkMode(self):
        return self._dark_mode

    @darkMode.setter
    def darkMode(self, value):
        if self._dark_mode != value:
            self._dark_mode = value
            self._apply_theme()
            self.themeChanged.emit(value)


# ----- Global Accessor Functions -----
def get_theme() -> ThemeManager:
    """Convenience function to get the ThemeManager singleton."""
    return ThemeManager.instance()

def apply_theme(widget, theme_mode: str):
    """Apply theme to a widget (legacy support for navigation.py).
    
    Args:
        widget: A QWidget to apply the theme to
        theme_mode: 'light', 'dark', or 'toggle' (uses ThemeManager's current mode)
    """
    manager = get_theme()
    if theme_mode == 'toggle':
        manager.toggle_theme()
    elif theme_mode == 'dark':
        manager.darkMode = True
    else:
        manager.darkMode = False