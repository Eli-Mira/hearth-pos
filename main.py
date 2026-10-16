"""Hearth POS - Main entry point."""
from __future__ import annotations

import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# Add the project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.engine import init_db
from app.ui.app_window import AppWindow
from app.seed import create_seed_data


def main():
    # Qt6 has high DPI scaling enabled by default
    # Set high DPI scale factor rounding policy (Qt6)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("Hearth POS")
    app.setApplicationVersion("0.1.0")

    # Set default font
    font = QFont("Inter", 10)
    app.setFont(font)

    # Initialize database
    init_db()

    # Run seed data if needed (it checks if data exists)
    create_seed_data()

    # Create and show main window
    window = AppWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())