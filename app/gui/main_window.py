"""
Main window for the Dune Companion PC App.

This module provides the primary application window with sidebar navigation,
menu bar, and content area for displaying different modules.
"""

from typing import Dict, Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QListWidget, QListWidgetItem, QStackedWidget,
    QLabel, QStatusBar, QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from .modules.resources_module import ResourcesModule
from .modules.crafting_module import CraftingModule
from .modules.settings_module import SettingsModule
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SidebarWidget(QListWidget):
    """Custom sidebar widget for navigation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        
        # Customize the sidebar appearance
        self.setStyleSheet("""
            QListWidget {
                background-color: rgba(30, 25, 20, 180);
                border: none;
                outline: none;
                font-size: 14px;
                font-weight: bold;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid rgba(100, 80, 60, 100);
                color: rgb(220, 200, 160);
            }
            QListWidget::item:selected {
                background-color: rgba(180, 120, 60, 150);
                color: rgb(45, 35, 25);
            }
            QListWidget::item:hover {
                background-color: rgba(120, 90, 60, 80);
            }
        """)


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation and content area."""
    
    # Signal emitted when the online status changes
    online_status_changed = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_module: Optional[QWidget] = None
        self.modules: Dict[str, QWidget] = {}
        self.is_online = False
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.load_modules()
        
        # Set window properties
        self.setWindowTitle("Dune Companion")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        logger.info("Main window initialized")
    
    def setup_ui(self) -> None:
        """Set up the main user interface layout."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for sidebar and content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.itemClicked.connect(self.on_sidebar_item_clicked)
        splitter.addWidget(self.sidebar)
        
        # Create content area
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("""
            QStackedWidget {
                background-color: rgba(60, 45, 30, 220);
                border-left: 2px solid rgba(100, 80, 60, 150);
            }
        """)
        splitter.addWidget(self.content_stack)
        
        # Set splitter proportions (sidebar smaller than content)
        splitter.setSizes([200, 800])
        splitter.setChildrenCollapsible(False)
        
        # Add navigation items
        self.add_navigation_items()
    
    def add_navigation_items(self) -> None:
        """Add navigation items to the sidebar."""
        navigation_items = [
            ("Resources", "Browse and manage game resources"),
            ("Crafting", "View crafting recipes and requirements"),
            ("Skill Tree", "Explore skill trees and builds"),
            ("Base Builder", "Plan and design base blueprints"),
            ("Lore & Wiki", "Browse game lore and wiki content"),
            ("AI Assistant", "Get AI-powered strategy help"),
            ("Settings", "Configure application settings")
        ]
        
        for title, tooltip in navigation_items:
            item = QListWidgetItem(title)
            item.setToolTip(tooltip)
            item.setData(Qt.ItemDataRole.UserRole, title.lower().replace(" ", "_").replace("&", ""))
            self.sidebar.addItem(item)
    
    def setup_menu_bar(self) -> None:
        """Set up the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Import data action
        import_action = QAction("&Import Data...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.setStatusTip("Import game data from JSON files")
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        # Export data action
        export_action = QAction("&Export Data...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export app data to JSON or Markdown")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Refresh action
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("Refresh current view")
        refresh_action.triggered.connect(self.refresh_current_module)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("About Dune Companion")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self) -> None:
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Online status indicator
        self.online_status_label = QLabel("Offline")
        self.online_status_label.setStyleSheet("""
            QLabel {
                color: rgb(180, 120, 60);
                font-weight: bold;
                padding: 2px 8px;
            }
        """)
        self.status_bar.addPermanentWidget(self.online_status_label)
        
        # Default status message
        self.status_bar.showMessage("Ready")
    
    def load_modules(self) -> None:
        """Load and initialize all application modules."""
        try:
            # Create placeholder for each module
            self.modules["resources"] = ResourcesModule(self)
            self.modules["crafting"] = CraftingModule(self)
            self.modules["skill_tree"] = self.create_placeholder_module("Skill Tree", "Skill tree planning coming soon...")
            self.modules["base_builder"] = self.create_placeholder_module("Base Builder", "Base blueprint designer coming soon...")
            self.modules["lore_&_wiki"] = self.create_placeholder_module("Lore & Wiki", "Lore and wiki browser coming soon...")
            self.modules["ai_assistant"] = self.create_placeholder_module("AI Assistant", "AI-powered strategy assistant coming soon...")
            self.modules["settings"] = SettingsModule(self)
            
            # Add modules to the stacked widget
            for module in self.modules.values():
                self.content_stack.addWidget(module)
            
            # Select the first item by default
            if self.sidebar.count() > 0:
                self.sidebar.setCurrentRow(0)
                self.on_sidebar_item_clicked(self.sidebar.item(0))
                
            logger.info(f"Loaded {len(self.modules)} application modules")
            
        except Exception as e:
            logger.error(f"Error loading modules: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load application modules: {e}")
    
    def create_placeholder_module(self, title: str, message: str) -> QWidget:
        """Create a placeholder widget for modules not yet implemented."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title label
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: rgb(180, 120, 60);
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title_label)
        
        # Message label
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: rgb(200, 180, 140);
                margin-bottom: 40px;
            }
        """)
        layout.addWidget(message_label)
        
        return widget
    
    def on_sidebar_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle sidebar item clicks to switch modules."""
        if not item:
            return
        
        module_key = item.data(Qt.ItemDataRole.UserRole)
        
        if module_key in self.modules:
            self.current_module = self.modules[module_key]
            self.content_stack.setCurrentWidget(self.current_module)
            self.status_bar.showMessage(f"Viewing {item.text()}")
            logger.debug(f"Switched to module: {module_key}")
    
    def refresh_current_module(self) -> None:
        """Refresh the currently displayed module."""
        if self.current_module and hasattr(self.current_module, 'refresh'):
            # Call refresh method if it exists
            getattr(self.current_module, 'refresh')()
            self.status_bar.showMessage("View refreshed", 2000)
    
    def import_data(self) -> None:
        """Handle data import from JSON files."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Import Game Data", 
            "", 
            "JSON files (*.json);;All files (*.*)"
        )
        
        if file_path:
            # TODO: Implement data import functionality
            QMessageBox.information(self, "Import Data", f"Data import from {file_path} will be implemented soon.")
            logger.info(f"User selected file for import: {file_path}")
    
    def export_data(self) -> None:
        """Handle data export to JSON or Markdown."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export App Data",
            "",
            "JSON files (*.json);;Markdown files (*.md);;All files (*.*)"
        )
        
        if file_path:
            # TODO: Implement data export functionality
            QMessageBox.information(self, "Export Data", f"Data export to {file_path} will be implemented soon.")
            logger.info(f"User selected file for export: {file_path}")
    
    def show_about(self) -> None:
        """Show the About dialog."""
        about_text = """
        <h2>Dune Companion PC App</h2>
        <p><strong>Version:</strong> 0.1.0</p>
        <p><strong>Description:</strong> An offline-first reference and planning tool for Dune: Awakening</p>
        <p><strong>Features:</strong></p>
        <ul>
            <li>Browse game resources and crafting recipes</li>
            <li>Plan skill trees and base blueprints</li>
            <li>Explore lore and wiki content</li>
            <li>AI-powered strategy assistance (when online)</li>
        </ul>
        <p><strong>Data:</strong> Fully functional offline with local SQLite database</p>
        """
        
        QMessageBox.about(self, "About Dune Companion", about_text)
    
    def update_online_status(self, is_online: bool) -> None:
        """Update the online status indicator."""
        self.is_online = is_online
        
        if is_online:
            self.online_status_label.setText("Online")
            self.online_status_label.setStyleSheet("""
                QLabel {
                    color: rgb(120, 180, 60);
                    font-weight: bold;
                    padding: 2px 8px;
                }
            """)
        else:
            self.online_status_label.setText("Offline")
            self.online_status_label.setStyleSheet("""
                QLabel {
                    color: rgb(180, 120, 60);
                    font-weight: bold;
                    padding: 2px 8px;
                }
            """)
        
        self.online_status_changed.emit(is_online)
    
    def closeEvent(self, event):
        """Handle the window close event."""
        logger.info("Main window closing")
        event.accept()
