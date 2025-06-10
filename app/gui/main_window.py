"""
Main window for the Dune Companion PC App.

This module provides the primary application window with sidebar navigation,
menu bar, and content area for displaying different modules.
"""

from typing import Dict, Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStackedWidget,
    QSplitter, QListWidgetItem, QStatusBar, QMessageBox, QFileDialog, QListWidget
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction # QAction is kept

from app.gui.modules.resources_module import ResourcesModule
from app.gui.modules.crafting_module import CraftingModule
from app.gui.modules.settings_module import SettingsModule
from app.gui.modules.ai_assistant_module import AIAssistantModule # Added import
from app.utils.logger import get_logger
from app.utils.network_utils import check_internet_connection

logger = get_logger(__name__)


class SidebarWidget(QListWidget):  # Added SidebarWidget class definition
    """Custom QListWidget for the sidebar navigation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200) # Example width, can be adjusted
        self.setStyleSheet("""
            QListWidget {
                background-color: rgba(30, 20, 10, 200); /* Darker, more thematic */
                border: none; /* Remove border if splitter handles separation */
                color: #FFF5D6; /* Cream color for text */
                font-size: 14px; /* Slightly larger font */
                padding-top: 10px; /* Space at the top */
            }
            QListWidget::item {
                padding: 12px 15px; /* More padding for items */
                border-bottom: 1px solid rgba(80, 60, 40, 100); /* Separator line */
            }
            QListWidget::item:selected {
                background-color: rgba(180, 120, 60, 180); /* More prominent selection */
                color: rgb(45, 35, 25); /* Dark text on selection */
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: rgba(120, 90, 60, 100); /* Subtle hover */
            }
        """)


class MainWindow(QMainWindow):
    online_status_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        
        self.current_module: Optional[QWidget] = None
        self.modules: Dict[str, QWidget] = {}
        self.is_online = False # Retained for potential direct checks if needed
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar() # This already calls update_status_bar() for initial check
        self.load_modules()
        
        # Set window properties
        self.setWindowTitle("Dune Companion")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Global button style
        self.setStyleSheet(self.styleSheet() + """QPushButton { 
            background-color: #FFF5D6; 
            color: rgb(45, 35, 25); 
            border: none; 
            border-radius: 4px; 
            font-weight: bold; 
        } 
        QPushButton:hover { 
            background-color: #FFE650; 
        } 
        QPushButton:pressed { 
            background-color: #FFE650; 
        }""")

        # Timer to periodically check connection status
        self.status_check_timer = QTimer(self)
        self.status_check_timer.timeout.connect(self.update_status_bar)
        self.status_check_timer.start(30000) # Check every 30 seconds (30000 ms)
        
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
        """Set up the status bar at the bottom of the window."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Connectivity Status Label (far left)
        self.status_label = QLabel("Status: Unknown")
        # Initial minimal styling; update_status_bar will set color and font-weight.
        self.status_label.setStyleSheet("padding: 2px 5px;") 
        self.status_bar.addWidget(self.status_label)

        # Current Action/View Label (center, will take available space)
        self.current_action_label = QLabel("") # Initially empty
        self.current_action_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Style to match module titles (yellow, bold)
        self.current_action_label.setStyleSheet("padding: 2px 10px; color: #FFE650; font-weight: bold;")
        self.status_bar.addWidget(self.current_action_label, 1) # Stretch factor of 1 to take available space

        # Version Label (far right, permanent)
        app_version = "0.1.0-alpha" # TODO: Replace with dynamic version later
        self.version_label = QLabel(f"Version: {app_version}")
        self.version_label.setStyleSheet("color: #A0A0A0; padding: 2px 5px;")
        self.status_bar.addPermanentWidget(self.version_label)

        # Call to set the initial text and style based on connectivity
        self.update_status_bar()
        # self.current_action_label can be set initially if needed, e.g., after first module loads
    
    def load_modules(self) -> None:
        """Load and initialize all application modules."""
        try:
            # Create placeholder for each module
            self.modules["resources"] = ResourcesModule(self)
            self.modules["crafting"] = CraftingModule(self)
            self.modules["skill_tree"] = self.create_placeholder_module("Skill Tree", "Skill tree planning coming soon...")
            self.modules["base_builder"] = self.create_placeholder_module("Base Builder", "Base blueprint designer coming soon...")
            self.modules["lore_&_wiki"] = self.create_placeholder_module("Lore & Wiki", "Lore and wiki browser coming soon...")
            self.modules["ai_assistant"] = AIAssistantModule(self) # Replaced placeholder
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
        main_module_layout = QVBoxLayout(widget) # Renamed for clarity
        main_module_layout.setContentsMargins(10, 0, 10, 10) # Standard module margins
        main_module_layout.setSpacing(0) # No space between header and content widget

        # Standard Module Header
        header_label = QLabel(title)
        header_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #FFE650;
                padding: 5px 0px;
                margin: 0px;
                border-bottom: 1px solid rgba(100, 80, 60, 150); /* Optional: adds a subtle separator */
            }
        """)
        header_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        main_module_layout.addWidget(header_label)

        # Content Area for the placeholder message
        content_widget = QWidget() # Specific widget for content below header
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setContentsMargins(0, 20, 0, 0) # Add some space above the message
        
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #FFF5D6; /* Cream color for placeholder message text */
                margin-bottom: 40px;
            }
        """)
        content_layout.addWidget(message_label)
        
        main_module_layout.addWidget(content_widget)
        main_module_layout.addStretch() # Push content to top if placeholder is simple
        
        return widget
    
    def on_sidebar_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle sidebar item clicks to switch modules."""
        if not item:
            return
        
        module_key = item.data(Qt.ItemDataRole.UserRole)
        
        if module_key in self.modules:
            self.current_module = self.modules[module_key]
            self.content_stack.setCurrentWidget(self.current_module)
            # self.status_bar.showMessage(f"Viewing {item.text()}") # OLD
            self.current_action_label.setText(f"Viewing {item.text()}") # NEW
            logger.debug(f"Switched to module: {module_key}. Current action label updated.")
    
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
    
    def update_status_bar(self) -> None:
        """Checks internet connection and updates the status bar label and style."""
        is_online = check_internet_connection()
        current_padding = "padding: 2px 5px;" # Define consistent padding
        if is_online:
            self.status_label.setText("Status: Online")
            self.status_label.setStyleSheet(f"color: #A1FFA1; {current_padding} font-weight: bold;")
        else:
            self.status_label.setText("Status: Offline")
            self.status_label.setStyleSheet(f"color: #FFA1A1; {current_padding} font-weight: bold;")
        
        self.online_status_changed.emit(is_online)
        logger.debug(f"Status bar updated: {self.status_label.text()}")
