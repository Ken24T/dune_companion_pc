\
# filepath: c:\\repos\\dune_companion_pc\\app\\gui\\modules\\ai_assistant_module.py
"""
AI Assistant module for the Dune Companion PC App.

This module provides an interface to interact with an AI model (e.g., OpenAI GPT)
for game-related questions and assistance.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QObject

from app.utils.logger import get_logger
from app.utils.ai_utils import get_ai_response, client as ai_client # Import client to check status
from app.utils.network_utils import check_internet_connection

logger = get_logger(__name__)

class AIWorker(QObject):
    """
    Worker thread for handling AI API calls asynchronously.
    """
    response_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, prompt: str, model: str = "gpt-3.5-turbo"):
        super().__init__()
        self.prompt = prompt
        self.model = model

    @Slot()
    def run(self):
        try:
            logger.info(f"AIWorker started for prompt: {self.prompt[:50]}...")
            response = get_ai_response(self.prompt, self.model)
            if response.startswith("Error:"):
                self.error_occurred.emit(response)
            else:
                self.response_ready.emit(response)
            logger.info(f"AIWorker finished for prompt: {self.prompt[:50]}...")
        except Exception as e:
            logger.error(f"Exception in AIWorker: {e}", exc_info=True)
            self.error_occurred.emit(f"An unexpected error occurred in the AI worker: {e}")

class AIAssistantModule(QWidget):
    """AI Assistant module widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent # Assuming parent is MainWindow to access online status
        self.is_online = False
        self.api_key_ok = False
        self.ai_thread = None
        self.ai_worker = None
        self.setup_ui()
        self.update_status_and_ui()

        if self.main_window and hasattr(self.main_window, 'online_status_changed'):
            self.main_window.online_status_changed.connect(self.handle_online_status_change)
            # Initial check based on main window's current status if available
            if hasattr(self.main_window, 'is_online'):
                 self.handle_online_status_change(self.main_window.is_online)


    def setup_ui(self) -> None:
        """Set up the AI Assistant module UI."""
        module_layout = QVBoxLayout(self)
        module_layout.setContentsMargins(10, 0, 10, 10)
        module_layout.setSpacing(10)

        # Header
        header_label = QLabel("AI Assistant")
        header_label.setStyleSheet("""
            padding: 5px 0px 5px 0px;
            color: #FFE650;
            font-weight: bold;
            font-size: 20px;
            margin: 0px;
        """)
        header_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        module_layout.addWidget(header_label)

        # Status Info Label
        self.status_info_label = QLabel("Status: Initializing...")
        self.status_info_label.setStyleSheet("font-style: italic; color: #A0A0A0; padding-bottom: 5px;")
        module_layout.addWidget(self.status_info_label)

        # Prompt Input Area
        prompt_group_layout = QHBoxLayout()
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Enter your question or prompt for the AI assistant...")
        self.prompt_input.setMinimumHeight(80)
        self.prompt_input.setStyleSheet("""
            QTextEdit {
                background-color: rgba(40, 30, 20, 200);
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                padding: 8px;
                color: #FFF5D6;
                font-size: 13px;
            }
        """)
        prompt_group_layout.addWidget(self.prompt_input, 4) # Give more stretch to text edit

        self.submit_button = QPushButton("Ask AI")
        self.submit_button.setMinimumHeight(80) # Match prompt input height
        self.submit_button.clicked.connect(self._on_submit_prompt)
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #FFF5D6; color: rgb(45, 35, 25);
                border: none; border-radius: 4px; padding: 10px 20px;
                font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #FFE650; }
            QPushButton:pressed { background-color: #FFE650; }
            QPushButton:disabled { background-color: #A0A0A0; color: #606060; }
        """)
        prompt_group_layout.addWidget(self.submit_button, 1) # Less stretch for button
        module_layout.addLayout(prompt_group_layout)

        # Response Area
        response_label = QLabel("AI Response:")
        response_label.setStyleSheet("font-weight: bold; color: #FFE650; margin-top: 10px;")
        module_layout.addWidget(response_label)

        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setStyleSheet("""
            QTextEdit {
                background-color: rgba(30, 20, 10, 230);
                border: 1px solid rgba(100, 80, 60, 150);
                border-radius: 4px;
                padding: 8px;
                color: #E0E0E0; /* Lighter text for readability */
                font-size: 13px;
            }
        """)
        module_layout.addWidget(self.response_area, 1) # Stretch factor for response area

        self.setLayout(module_layout)

    def update_status_and_ui(self):
        """Updates the status variables and enables/disables UI elements."""
        self.is_online = check_internet_connection()
        self.api_key_ok = ai_client is not None

        status_parts = []
        if self.is_online:
            status_parts.append("<font color=\'#A1FFA1\'>Online</font>")
        else:
            status_parts.append("<font color=\'#FFA1A1\'>Offline</font>")

        if self.api_key_ok:
            status_parts.append("API Key: <font color=\'#A1FFA1\'>OK</font>")
        else:
            status_parts.append("API Key: <font color=\'#FFA1A1\'>Missing/Invalid</font>")
        
        self.status_info_label.setText(f"Status: {', '.join(status_parts)}")

        can_submit = self.is_online and self.api_key_ok
        self.submit_button.setEnabled(can_submit)
        self.prompt_input.setEnabled(can_submit)
        if not can_submit:
            self.prompt_input.setPlaceholderText(
                "AI Assistant is unavailable. Check internet connection and API key in settings."
            )
        else:
            self.prompt_input.setPlaceholderText("Enter your question or prompt for the AI assistant...")
        logger.debug(f"AI Module UI updated: Online={self.is_online}, APIKeyOK={self.api_key_ok}, CanSubmit={can_submit}")


    @Slot(bool)
    def handle_online_status_change(self, is_online: bool):
        """Handles the online_status_changed signal from MainWindow."""
        logger.info(f"AI Module received online status change: {is_online}")
        self.is_online = is_online
        self.update_status_and_ui()

    def _on_submit_prompt(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Empty Prompt", "Please enter a question or prompt for the AI.")
            return

        if not self.is_online:
            QMessageBox.critical(self, "Offline", "Cannot connect to AI services. Please check your internet connection.")
            return
        
        if not self.api_key_ok:
            QMessageBox.critical(self, "API Key Error", "OpenAI API key is not configured or invalid. Please check settings.")
            return

        self.response_area.setText("<i>Thinking...</i>")
        self.submit_button.setEnabled(False)
        self.prompt_input.setEnabled(False)

        # Setup and start the AI worker thread
        self.ai_thread = QThread()
        self.ai_worker = AIWorker(prompt)
        self.ai_worker.moveToThread(self.ai_thread)

        self.ai_thread.started.connect(self.ai_worker.run)
        self.ai_worker.response_ready.connect(self._handle_ai_response)
        self.ai_worker.error_occurred.connect(self._handle_ai_error)
        
        # Clean up thread and worker when finished
        self.ai_worker.finished.connect(self.ai_thread.quit) # type: ignore
        self.ai_worker.finished.connect(self.ai_worker.deleteLater) # type: ignore
        self.ai_thread.finished.connect(self.ai_thread.deleteLater)
        
        self.ai_thread.start()
        logger.info(f"AI request submitted for prompt: {prompt[:50]}...")

    @Slot(str)
    def _handle_ai_response(self, response_text: str):
        self.response_area.setHtml(response_text.replace("\\n", "<br>")) # Basic HTML for newlines
        self.update_status_and_ui() # Re-enable inputs
        logger.info("AI response received and displayed.")

    @Slot(str)
    def _handle_ai_error(self, error_message: str):
        self.response_area.setHtml(f"<font color=\'#FFA1A1\'><b>Error:</b><br>{error_message}</font>")
        self.update_status_and_ui() # Re-enable inputs
        logger.error(f"AI error displayed: {error_message}")

    def refresh(self) -> None:
        """Refreshes the AI module (e.g., re-check status)."""
        logger.info("AI Assistant module refreshed.")
        self.update_status_and_ui()
        # Optionally clear prompt/response or provide other refresh actions
        # self.prompt_input.clear()
        # self.response_area.clear()

if __name__ == '__main__':
    # This part is for testing the module independently.
    # You would typically run the main application (main.py).
    import sys
    from PySide6.QtWidgets import QApplication

    class MockMainWindow(QWidget): # Minimal mock for testing signal connection
        online_status_changed = Signal(bool)
        def __init__(self):
            super().__init__()
            self.is_online = True # Simulate online status
            # In a real scenario, this would be updated by network checks

    app = QApplication(sys.argv)
    
    # To test API key status, ensure your OPENAI_API_KEY env var is set
    # or ai_utils.OPENAI_API_KEY is hardcoded (for testing only)
    if not ai_client:
        print("WARNING: OpenAI client not initialized. API key might be missing for standalone test.")

    mock_main = MockMainWindow()
    ai_module = AIAssistantModule(mock_main)
    ai_module.show()
    
    # Simulate online status change for testing
    # mock_main.online_status_changed.emit(False) # Test offline
    # mock_main.online_status_changed.emit(True)  # Test online

    sys.exit(app.exec())
