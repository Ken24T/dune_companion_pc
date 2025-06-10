"""
Resources module for the Dune Companion PC App.

This module provides the interface for browsing and managing game resources.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QTextEdit, QSplitter, QLabel, QLineEdit, QComboBox,
    QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6 import QtCore

from app.data.crud import get_all_resources
from app.data.models import Resource
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ResourceListWidget(QListWidget):
    """Custom list widget for displaying resources."""
    
    resource_selected = Signal(Resource)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resources: List[Resource] = []
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the resource list UI."""
        self.setStyleSheet("""
            QListWidget {
                background-color: rgba(45, 35, 25, 200);
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid rgba(80, 60, 40, 100);
                color: #FFF5D6;
            }
            QListWidget::item:selected {
                background-color: rgba(180, 120, 60, 150);
                color: rgb(45, 35, 25);
            }
            QListWidget::item:hover {
                background-color: rgba(120, 90, 60, 80);
            }
        """)
        
        self.itemClicked.connect(self.on_item_clicked)
    
    def load_resources(self, resources: List[Resource]) -> None:
        """Load resources into the list."""
        self.clear()
        self.resources = resources
        
        for resource in resources:
            item = QListWidgetItem(resource.name)
            item.setData(Qt.ItemDataRole.UserRole, resource.id)
            if resource.category:
                item.setToolTip(f"Category: {resource.category}")
            self.addItem(item)
    
    def on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle resource item clicks."""
        resource_id = item.data(Qt.ItemDataRole.UserRole)
        resource = next((r for r in self.resources if r.id == resource_id), None)
        if resource:
            self.resource_selected.emit(resource)


class ResourceDetailWidget(QWidget):
    """Widget for displaying detailed resource information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_resource: Optional[Resource] = None
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the resource detail UI."""
        layout = QVBoxLayout(self)
        
        # Title
        self.title_label = QLabel("Select a resource to view details")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #FFE650;
                padding: 10px;
                border-bottom: 2px solid rgba(100, 80, 60, 150);
            }
        """)
        layout.addWidget(self.title_label)
        
        # Scroll area for details
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.detail_widget)
        layout.addWidget(scroll_area)
        
        # Initially hide details
        self.detail_widget.hide()
    
    def display_resource(self, resource: Resource) -> None:
        """Display detailed information about a resource."""
        self.current_resource = resource
        self.title_label.setText(resource.name)
        
        # Clear existing details
        for i in reversed(range(self.detail_layout.count())):
            child = self.detail_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add resource details
        self.add_detail_group("Basic Information", [
            ("Name", resource.name),
            ("Category", resource.category or "Unknown"),
            ("Rarity", resource.rarity or "Common"),
            ("Icon Path", resource.icon_path or "Not set")
        ])
        
        if resource.description:
            self.add_description_group("Description", resource.description)
        
        # if resource.gathering_info:
        #     self.add_description_group("Gathering Information", resource.gathering_info)
        
        # if resource.usage_info:
        #     self.add_description_group("Usage Information", resource.usage_info)
        
        self.add_detail_group("Metadata", [
            ("Created", resource.created_at or "Unknown"),
            ("Updated", resource.updated_at or "Unknown")
        ])
        
        self.detail_widget.show()
    
    def add_detail_group(self, title: str, details: List[tuple]) -> None:
        """Add a group of detail information."""
        group_box = QGroupBox(title)
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                color: #FFE650;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group_box)
        
        for label, value in details:
            if value:
                detail_layout = QHBoxLayout()
                
                label_widget = QLabel(f"{label}:")
                label_widget.setStyleSheet("font-weight: bold; color: #FFE650;")
                label_widget.setFixedWidth(120)
                detail_layout.addWidget(label_widget)
                
                value_widget = QLabel(str(value))
                value_widget.setStyleSheet("color: #FFF5D6;")
                value_widget.setWordWrap(True)
                detail_layout.addWidget(value_widget)
                
                layout.addLayout(detail_layout)
        
        self.detail_layout.addWidget(group_box)
    
    def add_description_group(self, title: str, description: str) -> None:
        """Add a description text group."""
        group_box = QGroupBox(title)
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                color: #FFE650;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group_box)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(description)
        text_edit.setReadOnly(True)
        text_edit.setMaximumHeight(100)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(60, 45, 30, 150);
                border: 1px solid rgba(80, 60, 40, 100);
                border-radius: 4px;
                padding: 8px;
                color: #FFF5D6;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(text_edit)
        self.detail_layout.addWidget(group_box)


class ResourcesModule(QWidget):
    """Main resources module widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_resources()
    
    def setup_ui(self) -> None:
        """Set up the resources module UI with a simplified layout structure."""
        module_layout = QVBoxLayout(self)
        # Overall padding for the module pane. Top is 0; header_label handles its own top padding.
        module_layout.setContentsMargins(10, 0, 10, 10) 
        module_layout.setSpacing(0) # Default spacing between items added to module_layout

        # --- Header ---
        header_label = QLabel("Resources")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #FFE650;
                padding: 5px 0px 5px 0px; /* 5px top, 5px bottom, 0px sides */
                margin: 0;
            }
        """)
        header_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        module_layout.addWidget(header_label) # Stretch factor 0 (default)

        # --- Controls ---
        # Search and filter controls (within their own widget for horizontal layout)
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0) # No extra margins for the controls widget itself
        controls_layout.setSpacing(5) # Horizontal spacing for search/category items

        # Create search label and box first
        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: #FFE650; font-weight: bold;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search resources...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 45, 30, 150);
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                padding: 6px;
                color: #FFF5D6;
                font-size: 12px;
            }
        """)
        self.search_box.textChanged.connect(self.filter_resources)
        # self.search_box.setFixedWidth(300) 

        # Group search label and search box into a fixed-width widget
        search_group_widget = QWidget()
        search_group_layout = QHBoxLayout(search_group_widget)
        search_group_layout.setContentsMargins(0, 0, 0, 0)
        search_group_layout.setSpacing(5) # Internal spacing for search label and box
        search_group_layout.addWidget(search_label)
        search_group_layout.addWidget(self.search_box) # search_box will expand within this group
        search_group_widget.setFixedWidth(300)

        controls_layout.addWidget(search_group_widget) # Add the group to the main controls layout
        controls_layout.addSpacing(20) # Changed to 20px spacing after the search group

        category_label = QLabel("Category:")
        category_label.setStyleSheet("color: #FFE650; font-weight: bold;")
        controls_layout.addWidget(category_label)

        self.category_filter = QComboBox()
        self.category_filter.setStyleSheet("""
            QComboBox {
                background-color: rgba(60, 45, 30, 150);
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                padding: 6px;
                color: #FFF5D6;
                font-size: 12px;
            }
            QComboBox QAbstractItemView { 
                background-color: rgba(45, 35, 25, 255); 
                color: #FFF5D6;
                selection-background-color: rgba(180, 120, 60, 150);
            }
        """)
        self.category_filter.currentTextChanged.connect(self.filter_resources)
        controls_layout.addWidget(self.category_filter)
        
        controls_layout.addStretch() 
        module_layout.addWidget(controls_widget) # Stretch factor 0 (default)

        # Add a defined space between controls and the splitter
        module_layout.addSpacing(8) 

        # --- Main Content Area (Splitter) ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.resource_list = ResourceListWidget()
        self.resource_list.resource_selected.connect(self.on_resource_selected)
        splitter.addWidget(self.resource_list)

        self.resource_detail = ResourceDetailWidget()
        splitter.addWidget(self.resource_detail)
        splitter.setSizes([300, 500]) # Initial sizes for list and detail panes
        
        # Add splitter to the main layout with a stretch factor to fill remaining space
        module_layout.addWidget(splitter, 1)
    
    def load_resources(self) -> None:
        """Load resources from the database."""
        try:
            from app.data.database import get_default_db_path
            db_path = get_default_db_path()
            
            resources = get_all_resources(db_path)
            self.all_resources = resources
            self.resource_list.load_resources(resources)
            
            # Populate category filter
            categories = set()
            for resource in resources:
                if resource.category:
                    categories.add(resource.category)
            
            self.category_filter.clear()
            self.category_filter.addItem("All Categories")
            for category in sorted(categories):
                self.category_filter.addItem(category)
            
            logger.info(f"Loaded {len(resources)} resources")
            
        except Exception as e:
            logger.error(f"Error loading resources: {e}", exc_info=True)
            self.all_resources = []
    
    def filter_resources(self) -> None:
        """Filter resources based on search and category filters."""
        if not hasattr(self, 'all_resources'):
            return
        
        search_text = self.search_box.text().lower()
        category_filter = self.category_filter.currentText()
        
        filtered_resources = []
        for resource in self.all_resources:
            # Check search filter
            if search_text and search_text not in resource.name.lower():
                if not resource.description or search_text not in resource.description.lower():
                    continue
            
            # Check category filter
            if category_filter != "All Categories":
                if resource.category != category_filter:
                    continue
            
            filtered_resources.append(resource)
        
        self.resource_list.load_resources(filtered_resources)
    
    def on_resource_selected(self, resource: Resource) -> None:
        """Handle resource selection."""
        self.resource_detail.display_resource(resource)
        logger.debug(f"Selected resource: {resource.name}")
    
    def refresh(self) -> None:
        """Refresh the module data."""
        self.load_resources()
        logger.info("Resources module refreshed")
