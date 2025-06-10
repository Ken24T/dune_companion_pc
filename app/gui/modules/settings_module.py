"""
Settings module for the Dune Companion PC App.

This module provides the interface for configuring application settings.
"""

from typing import Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QCheckBox, QLineEdit, QSpinBox, QComboBox,
    QFileDialog, QMessageBox, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from app.utils.logger import get_logger

logger = get_logger(__name__)


class SettingsModule(QWidget):
    """Main settings module widget."""
    
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = self.load_default_settings()
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the settings module UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 10) # Top margin 0 for the main layout
        layout.setSpacing(0) # No space between header and scroll_area
        
        # Header
        header_label = QLabel("Settings")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #FFE650;
                padding: 5px 0px; 
                margin: 0px;
            }
        """)
        header_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(header_label)
        
        # Scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Add a small top padding inside the scroll area, and spacing between group boxes
        settings_layout.setContentsMargins(0, 5, 0, 5) # 5px top padding
        settings_layout.setSpacing(10) # 10px spacing between items (group boxes)
        
        # Database settings
        self.add_database_settings(settings_layout)
        
        # Import/Export settings
        self.add_import_export_settings(settings_layout)
        
        # UI settings
        self.add_ui_settings(settings_layout)
        
        # AI Assistant settings
        self.add_ai_settings(settings_layout)
        
        # About section
        self.add_about_section(settings_layout)
        
        # Save button
        save_button = QPushButton("Save Settings")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #FFF5D6;
                color: rgb(45, 35, 25);
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FFE650;
            }
            QPushButton:pressed {
                background-color: #FFE650;
            }
        """)
        save_button.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_button)
        
        scroll_area.setWidget(settings_widget)
        layout.addWidget(scroll_area)
    
    def add_database_settings(self, layout: QVBoxLayout) -> None:
        """Add database-related settings."""
        group_box = QGroupBox("Database Settings")
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                /* margin-top: 10px; */ /* Removed, spacing handled by parent layout */
                padding-top: 10px;
                color: #FFE650;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        group_layout = QVBoxLayout(group_box)
        
        # Database path
        db_layout = QHBoxLayout()
        db_label = QLabel("Database Path:")
        db_label.setStyleSheet("color: rgb(200, 180, 140); font-weight: bold;")
        db_layout.addWidget(db_label)
        
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setText(self.settings.get('database_path', 'data/dune_companion.db'))
        self.db_path_edit.setReadOnly(True)
        self.db_path_edit.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 45, 30, 150);
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                padding: 6px;
                color: rgb(220, 200, 160);
                font-size: 12px;
            }
        """)
        db_layout.addWidget(self.db_path_edit)
        
        browse_button = QPushButton("Browse...")
        browse_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(120, 90, 60, 150);
                color: rgb(220, 200, 160);
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(120, 90, 60, 200);
            }
        """)
        browse_button.clicked.connect(self.browse_database_path)
        db_layout.addWidget(browse_button)
        
        group_layout.addLayout(db_layout)
        
        # Auto-backup option
        self.auto_backup_check = QCheckBox("Enable automatic database backups")
        self.auto_backup_check.setChecked(self.settings.get('auto_backup', True))
        self.auto_backup_check.setStyleSheet("""
            QCheckBox {
                color: rgb(220, 200, 160);
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        group_layout.addWidget(self.auto_backup_check)
        
        layout.addWidget(group_box)
    
    def add_import_export_settings(self, layout: QVBoxLayout) -> None:
        """Add import/export settings."""
        group_box = QGroupBox("Import/Export Settings")
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                /* margin-top: 10px; */ /* Removed, spacing handled by parent layout */
                padding-top: 10px;
                color: #FFE650;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        group_layout = QVBoxLayout(group_box)
        
        # Default export format
        format_layout = QHBoxLayout()
        format_label = QLabel("Default Export Format:")
        format_label.setStyleSheet("color: rgb(200, 180, 140); font-weight: bold;")
        format_layout.addWidget(format_label)
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["JSON", "Markdown", "Both"])
        self.export_format_combo.setCurrentText(self.settings.get('default_export_format', 'JSON'))
        self.export_format_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(60, 45, 30, 150);
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                padding: 6px;
                color: rgb(220, 200, 160);
                font-size: 12px;
            }
        """)
        format_layout.addWidget(self.export_format_combo)
        format_layout.addStretch()
        
        group_layout.addLayout(format_layout)
        
        # Include metadata option
        self.include_metadata_check = QCheckBox("Include metadata in exports")
        self.include_metadata_check.setChecked(self.settings.get('include_metadata', True))
        self.include_metadata_check.setStyleSheet("""
            QCheckBox {
                color: rgb(220, 200, 160);
                font-size: 12px;
            }
        """)
        group_layout.addWidget(self.include_metadata_check)
        
        layout.addWidget(group_box)
    
    def add_ui_settings(self, layout: QVBoxLayout) -> None:
        """Add UI customization settings."""
        group_box = QGroupBox("UI Settings")
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                /* margin-top: 10px; */ /* Removed, spacing handled by parent layout */
                padding-top: 10px;
                color: #FFE650;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        group_layout = QVBoxLayout(group_box)
        
        # Font size
        font_layout = QHBoxLayout()
        font_label = QLabel("Font Size:")
        font_label.setStyleSheet("color: rgb(200, 180, 140); font-weight: bold;")
        font_layout.addWidget(font_label)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.settings.get('font_size', 12))
        self.font_size_spin.setStyleSheet("""
            QSpinBox {
                background-color: rgba(60, 45, 30, 150);
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                padding: 6px;
                color: rgb(220, 200, 160);
                font-size: 12px;
            }
        """)
        font_layout.addWidget(self.font_size_spin)
        font_layout.addStretch()
        
        group_layout.addLayout(font_layout)
        
        # Remember window size
        self.remember_window_check = QCheckBox("Remember window size and position")
        self.remember_window_check.setChecked(self.settings.get('remember_window', True))
        self.remember_window_check.setStyleSheet("""
            QCheckBox {
                color: rgb(220, 200, 160);
                font-size: 12px;
            }
        """)
        group_layout.addWidget(self.remember_window_check)
        
        layout.addWidget(group_box)
    
    def add_ai_settings(self, layout: QVBoxLayout) -> None:
        """Add AI Assistant settings."""
        group_box = QGroupBox("AI Assistant Settings")
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                /* margin-top: 10px; */ /* Removed, spacing handled by parent layout */
                padding-top: 10px;
                color: #FFE650;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        group_layout = QVBoxLayout(group_box)
        
        # Enable AI Assistant
        self.ai_enabled_check = QCheckBox("Enable AI Assistant (requires internet)")
        self.ai_enabled_check.setChecked(self.settings.get('ai_enabled', False))
        self.ai_enabled_check.setStyleSheet("""
            QCheckBox {
                color: rgb(220, 200, 160);
                font-size: 12px;
            }
        """)
        group_layout.addWidget(self.ai_enabled_check)
        
        # API Key (placeholder)
        api_layout = QHBoxLayout()
        api_label = QLabel("API Key:")
        api_label.setStyleSheet("color: rgb(200, 180, 140); font-weight: bold;")
        api_layout.addWidget(api_label)
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Enter OpenAI API key (optional)")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setStyleSheet("""
            QLineEdit {
                background-color: rgba(60, 45, 30, 150);
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                padding: 6px;
                color: rgb(220, 200, 160);
                font-size: 12px;
            }
        """)
        api_layout.addWidget(self.api_key_edit)
        
        group_layout.addLayout(api_layout)
        
        layout.addWidget(group_box)
    
    def add_about_section(self, layout: QVBoxLayout) -> None:
        """Add About section."""
        group_box = QGroupBox("About")
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                /* margin-top: 10px; */ /* Removed, spacing handled by parent layout */
                padding-top: 10px;
                color: #FFE650;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        group_layout = QVBoxLayout(group_box)
        
        about_text = QTextEdit()
        about_text.setPlainText(
            "Dune Companion PC App v0.1.0\n\n"
            "An offline-first reference and planning tool for Dune: Awakening.\n\n"
            "Features:\n"
            "• Browse game resources and crafting recipes\n"
            "• Plan skill trees and base blueprints\n"
            "• Explore lore and wiki content\n"
            "• AI-powered strategy assistance (when online)\n"
            "• Export data to JSON and Markdown formats\n\n"
            "Built with Python and PySide6.\n"
            "All data stored locally in SQLite database."
        )
        about_text.setReadOnly(True)
        about_text.setMaximumHeight(150)
        about_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(60, 45, 30, 150);
                border: 1px solid rgba(80, 60, 40, 100);
                border-radius: 4px;
                padding: 8px;
                color: rgb(220, 200, 160);
                font-size: 12px;
            }
        """)
        
        group_layout.addWidget(about_text)
        layout.addWidget(group_box)
    
    def browse_database_path(self) -> None:
        """Browse for database file path."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Database File",
            self.db_path_edit.text(),
            "SQLite Database (*.db);;All files (*.*)"
        )
        
        if file_path:
            self.db_path_edit.setText(file_path)
            logger.info(f"Database path changed to: {file_path}")
    
    def load_default_settings(self) -> Dict[str, Any]:
        """Load default application settings."""
        return {
            'database_path': 'data/dune_companion.db',
            'auto_backup': True,
            'default_export_format': 'JSON',
            'include_metadata': True,
            'font_size': 12,
            'remember_window': True,
            'ai_enabled': False
        }
    
    def save_settings(self) -> None:
        """Save current settings."""
        self.settings = {
            'database_path': self.db_path_edit.text(),
            'auto_backup': self.auto_backup_check.isChecked(),
            'default_export_format': self.export_format_combo.currentText(),
            'include_metadata': self.include_metadata_check.isChecked(),
            'font_size': self.font_size_spin.value(),
            'remember_window': self.remember_window_check.isChecked(),
            'ai_enabled': self.ai_enabled_check.isChecked()
        }
        
        # TODO: Save settings to file
        self.settings_changed.emit(self.settings)
        
        QMessageBox.information(
            self,
            "Settings Saved",
            "Settings have been saved successfully.\nSome changes may require restarting the application."
        )
        
        logger.info("Settings saved successfully")
    
    def refresh(self) -> None:
        """Refresh the settings module."""
        logger.info("Settings module refreshed")
