#!/usr/bin/env python3
"""
Main entry point for the Dune Companion PC App.

This module initializes and runs the PySide6 GUI application.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from app.gui.main_window import MainWindow
from app.utils.logger import get_logger

# Add the project root to the Python path for app imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Get the app directory for asset paths
app_dir = Path(__file__).parent

logger = get_logger(__name__)


def setup_application_properties(app: QApplication) -> None:
    """Set up application-wide properties and metadata."""
    app.setApplicationName("Dune Companion")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Dune Companion")
    app.setOrganizationDomain("dune-companion.local")
    
    # Set application icon if available
    icon_path = app_dir.parent / "assets" / "icons" / "app_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))


def setup_application_style(app: QApplication) -> None:
    """Apply the Dune theme and styling to the application."""
    # For now, use a basic dark theme that fits the Dune aesthetic
    # This will be expanded with custom styling later
    app.setStyle("Fusion")
    
    # Apply basic Dune-inspired color palette
    palette = app.palette()
    
    # Dune desert/sand colors with dark accents
    from PySide6.QtGui import QColor, QPalette
    
    # Base color scheme - desert/sand tones with dark elements
    base_color = QColor(45, 35, 25)          # Dark brown base
    alt_base_color = QColor(60, 45, 30)      # Slightly lighter brown
    # Brighter yellow for text for more contrast
    text_color = QColor(255, 230, 80)        # Bright yellow text
    highlight_color = QColor(180, 120, 60)   # Orange/amber highlight (unchanged)
    disabled_color = QColor(120, 100, 80)    # Muted brown
    
    palette.setColor(QPalette.ColorRole.Window, base_color)
    palette.setColor(QPalette.ColorRole.WindowText, text_color)
    palette.setColor(QPalette.ColorRole.Base, alt_base_color)
    palette.setColor(QPalette.ColorRole.AlternateBase, base_color)
    palette.setColor(QPalette.ColorRole.Text, text_color)
    palette.setColor(QPalette.ColorRole.Button, alt_base_color)
    palette.setColor(QPalette.ColorRole.ButtonText, text_color)
    palette.setColor(QPalette.ColorRole.Highlight, highlight_color)
    palette.setColor(QPalette.ColorRole.HighlightedText, base_color)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color)
    
    app.setPalette(palette)


def main() -> int:
    """Main application entry point."""
    try:
        logger.info("Starting Dune Companion PC App")
        
        # Create the QApplication instance
        app = QApplication(sys.argv)
        
        # Set up application properties
        setup_application_properties(app)
        
        # Apply Dune theme
        setup_application_style(app)
        
        # Create and show the main window
        main_window = MainWindow()
        main_window.show()
        
        logger.info("Main window displayed, entering event loop")
        
        # Start the application event loop
        exit_code = app.exec()
        
        logger.info(f"Application exiting with code: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"Fatal error starting application: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())