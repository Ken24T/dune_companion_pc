"""
Crafting module for the Dune Companion PC App.

This module provides the interface for browsing and managing crafting recipes.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QTextEdit, QSplitter, QLabel, QLineEdit, QComboBox,
    QGroupBox, QScrollArea, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, Signal

from app.data.crud import get_all_crafting_recipes
from app.data.models import CraftingRecipe
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CraftingListWidget(QListWidget):
    """Custom list widget for displaying crafting recipes."""
    
    recipe_selected = Signal(CraftingRecipe)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recipes: List[CraftingRecipe] = []
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the crafting recipe list UI."""
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
        
        self.itemClicked.connect(self.on_item_clicked)
    
    def load_recipes(self, recipes: List[CraftingRecipe]) -> None:
        """Load crafting recipes into the list."""
        self.clear()
        self.recipes = recipes
        for recipe in recipes:
            item = QListWidgetItem(recipe.name)
            item.setData(Qt.ItemDataRole.UserRole, recipe.id)
            if recipe.description:
                item.setToolTip(recipe.description)
            self.addItem(item)
    
    def on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle recipe item clicks."""
        recipe_id = item.data(Qt.ItemDataRole.UserRole)
        recipe = next((r for r in self.recipes if r.id == recipe_id), None)
        if recipe:
            self.recipe_selected.emit(recipe)


class CraftingDetailWidget(QWidget):
    """Widget for displaying detailed crafting recipe information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_recipe: Optional[CraftingRecipe] = None
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the crafting recipe detail UI."""
        layout = QVBoxLayout(self)
        
        # Title
        self.title_label = QLabel("Select a crafting recipe to view details")
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
        self.detail_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.detail_widget)
        layout.addWidget(scroll_area)
        
        # Initially hide details
        self.detail_widget.hide()
    
    def display_recipe(self, recipe: CraftingRecipe) -> None:
        """Display detailed information about a crafting recipe."""
        self.current_recipe = recipe
        self.title_label.setText(recipe.name)
        
        # Clear existing details
        for i in reversed(range(self.detail_layout.count())):
            child = self.detail_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add recipe details
        self.add_detail_group("Basic Information", [
            ("Name", recipe.name),
            ("Required Station", recipe.required_station or "Any"),
            ("Output Quantity", recipe.output_quantity or 1),
            ("Crafting Time", f"{recipe.crafting_time_seconds or 0} seconds" if recipe.crafting_time_seconds else "Unknown"),
            ("Required Station", recipe.required_station or "Any"),
            ("Skill Requirement", recipe.skill_requirement or "None")
        ])
        
        if recipe.description:
            self.add_description_group("Description", recipe.description)
        
        # Add ingredients table
        if recipe.ingredients:
            self.add_ingredients_table(recipe.ingredients)
        
        self.add_detail_group("Metadata", [
            ("Created", recipe.created_at or "Unknown"),
            ("Updated", recipe.updated_at or "Unknown")
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
                value_widget.setStyleSheet("color: #FFE650;")
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
                color: #FFE650;
                font-size: 12px;
            }
        """)
        
        layout.addWidget(text_edit)
        self.detail_layout.addWidget(group_box)


    def add_ingredients_table(self, ingredients: List) -> None:
        """Add a table showing recipe ingredients."""
        group_box = QGroupBox("Ingredients")
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
        
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Resource", "Quantity"])
        table.setRowCount(len(ingredients))
        
        table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(60, 45, 30, 150);
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                color: rgb(220, 200, 160);
                gridline-color: rgba(80, 60, 40, 100);
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(80, 60, 40, 50);
            }
            QHeaderView::section {
                background-color: rgba(45, 35, 25, 200);
                color: rgb(180, 120, 60);
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        for i, ingredient in enumerate(ingredients):
            # Handle both RecipeIngredient objects and dict formats
            if hasattr(ingredient, 'resource_name'):
                # RecipeIngredient object
                name_item = QTableWidgetItem(ingredient.resource_name or 'Unknown')
                quantity_item = QTableWidgetItem(str(ingredient.quantity))
            else:
                # Dictionary format
                name_item = QTableWidgetItem(ingredient.get('resource_name', 'Unknown'))
                quantity_item = QTableWidgetItem(str(ingredient.get('quantity', 1)))
            
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(i, 0, name_item)
            
            quantity_item.setFlags(quantity_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(i, 1, quantity_item)
        
        table.resizeColumnsToContents()
        table.setMaximumHeight(200)
        
        layout.addWidget(table)
        self.detail_layout.addWidget(group_box)


class CraftingModule(QWidget):
    """Main crafting module widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_recipes()
    
    def setup_ui(self) -> None:
        """Set up the crafting module UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_label = QLabel("Crafting Recipes")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #FFE650;
                padding: 10px 0;
            }
        """)
        layout.addWidget(header_label)
        
        # Search and filter controls
        controls_layout = QHBoxLayout()
        
        # Search box
        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: #FFE650; font-weight: bold;")
        controls_layout.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search recipes...")
        self.search_box.textChanged.connect(self.filter_recipes)
        controls_layout.addWidget(self.search_box)

        category_label = QLabel("Category:")
        category_label.setStyleSheet("color: #FFE650; font-weight: bold;")
        controls_layout.addWidget(category_label)

        self.category_filter = QComboBox()
        self.category_filter.currentIndexChanged.connect(self.filter_recipes)
        controls_layout.addWidget(self.category_filter)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Main content area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Recipe list
        self.recipe_list = CraftingListWidget()
        self.recipe_list.recipe_selected.connect(self.on_recipe_selected)
        splitter.addWidget(self.recipe_list)
          # Recipe details
        self.recipe_detail = CraftingDetailWidget()
        splitter.addWidget(self.recipe_detail)
        
        # Set splitter proportions
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        # Global button style for this module
        self.setStyleSheet(self.styleSheet() + "\nQPushButton { background-color: #FFF5D6; color: rgb(45, 35, 25); border: none; border-radius: 4px; font-weight: bold; } QPushButton:hover { background-color: #FFE650; } QPushButton:pressed { background-color: #FFE650; }")
    
    def load_recipes(self) -> None:
        """Load crafting recipes from the database."""
        try:
            from app.data.database import get_default_db_path
            db_path = get_default_db_path()
            
            recipes = get_all_crafting_recipes(db_path)
            self.all_recipes = recipes
            self.recipe_list.load_recipes(recipes)
            
            # For now, just add "All Categories" since CraftingRecipe doesn't have categories
            self.category_filter.clear()
            self.category_filter.addItem("All Categories")
            
            logger.info(f"Loaded {len(recipes)} crafting recipes")
            
        except Exception as e:
            logger.error(f"Error loading crafting recipes: {e}", exc_info=True)
            self.all_recipes = []
    
    def filter_recipes(self) -> None:
        """Filter recipes based on search and category filters."""
        if not hasattr(self, 'all_recipes'):
            return
        
        search_text = self.search_box.text().lower()
        self.category_filter.currentText()
        
        filtered_recipes = []
        for recipe in self.all_recipes:            # Check search filter
            if search_text and search_text not in recipe.name.lower():
                if not recipe.description or search_text not in recipe.description.lower():
                    continue
            
            # Category filter is simplified since CraftingRecipe doesn't have categories
            # All recipes pass the category filter for now
            
            filtered_recipes.append(recipe)
        
        self.recipe_list.load_recipes(filtered_recipes)
    
    def on_recipe_selected(self, recipe: CraftingRecipe) -> None:
        """Handle recipe selection."""
        self.recipe_detail.display_recipe(recipe)
        logger.debug(f"Selected recipe: {recipe.name}")
    
    def refresh(self) -> None:
        """Refresh the module data."""
        self.load_recipes()
        logger.info("Crafting module refreshed")
