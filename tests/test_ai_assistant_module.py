import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Adjust path to import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Signal, QThread # Ensure QThread is imported for spec

# Modules to test
from app.gui.modules.ai_assistant_module import AIAssistantModule, AIWorker # Ensure AIWorker is imported for spec
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Minimal MainWindow mock for testing signals
class MockMainWindow(QWidget):
    online_status_changed = Signal(bool)
    is_online = True # Default to online for initial status

    def __init__(self):
        super().__init__()

class TestAIAssistantModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # QApplication instance is required for PySide6 widgets
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        self.mock_main_window = MockMainWindow()
        
        # Patch external dependencies
        self.patch_check_internet = patch('app.gui.modules.ai_assistant_module.check_internet_connection')
        self.mock_check_internet = self.patch_check_internet.start()

        self.patch_ai_client = patch('app.gui.modules.ai_assistant_module.ai_client')
        self.mock_ai_client_instance = self.patch_ai_client.start()
        
        self.patch_get_ai_response = patch('app.gui.modules.ai_assistant_module.get_ai_response')
        self.mock_get_ai_response = self.patch_get_ai_response.start()

        self.patch_qmessagebox = patch('app.gui.modules.ai_assistant_module.QMessageBox')
        self.mock_qmessagebox = self.patch_qmessagebox.start()

        # Create the module instance, passing the mock main window
        self.module = AIAssistantModule(parent=self.mock_main_window)

    def tearDown(self):
        self.patch_check_internet.stop()
        self.patch_ai_client.stop()
        self.patch_get_ai_response.stop()
        self.patch_qmessagebox.stop()
        self.module.deleteLater() # Ensure widget is cleaned up

    def test_initialization_ui_setup(self):
        logger.info("Running test_initialization_ui_setup")
        self.assertIsNotNone(self.module.status_info_label)
        self.assertIsNotNone(self.module.prompt_input)
        self.assertIsNotNone(self.module.submit_button)
        self.assertIsNotNone(self.module.response_area)
        self.assertTrue(self.module.status_info_label.text().startswith("Status:"))
        logger.info("Finished test_initialization_ui_setup")

    def test_update_status_and_ui_all_ok(self):
        logger.info("Running test_update_status_and_ui_all_ok")
        self.mock_check_internet.return_value = True
        # Simulate ai_client being successfully initialized (not None)
        # The patch_ai_client already makes ai_client a MagicMock, which is not None.
        # If ai_client itself was None, we'd mock app.utils.ai_utils.client directly
        
        self.module.update_status_and_ui()
        
        self.assertIn("Online", self.module.status_info_label.text())
        self.assertIn("API Key: <font color=\'#A1FFA1\'>OK</font>", self.module.status_info_label.text())
        self.assertTrue(self.module.submit_button.isEnabled())
        self.assertTrue(self.module.prompt_input.isEnabled())
        self.assertEqual(self.module.prompt_input.placeholderText(), "Enter your question or prompt for the AI assistant...")
        logger.info("Finished test_update_status_and_ui_all_ok")

    def test_update_status_and_ui_offline(self):
        logger.info("Running test_update_status_and_ui_offline")
        self.mock_check_internet.return_value = False
        # API key is OK
        
        self.module.update_status_and_ui()
        
        self.assertIn("Offline", self.module.status_info_label.text())
        self.assertIn("API Key: <font color=\'#A1FFA1\'>OK</font>", self.module.status_info_label.text()) # API key status should still be checked
        self.assertFalse(self.module.submit_button.isEnabled())
        self.assertFalse(self.module.prompt_input.isEnabled())
        self.assertIn("AI Assistant is unavailable", self.module.prompt_input.placeholderText())
        logger.info("Finished test_update_status_and_ui_offline")

    def test_update_status_and_ui_no_api_key(self):
        logger.info("Running test_update_status_and_ui_no_api_key")
        self.mock_check_internet.return_value = True
        self.mock_ai_client_instance = None # Simulate ai_client being None
        
        # We need to re-patch 'app.gui.modules.ai_assistant_module.ai_client' for this specific test case
        # because the setUp's patcher has already started.
        with patch('app.gui.modules.ai_assistant_module.ai_client', None):
            self.module.update_status_and_ui()
        
        self.assertIn("Online", self.module.status_info_label.text())
        self.assertIn("API Key: <font color=\'#FFA1A1\'>Missing/Invalid</font>", self.module.status_info_label.text())
        self.assertFalse(self.module.submit_button.isEnabled())
        self.assertFalse(self.module.prompt_input.isEnabled())
        self.assertIn("AI Assistant is unavailable", self.module.prompt_input.placeholderText())
        logger.info("Finished test_update_status_and_ui_no_api_key")

    def test_handle_online_status_change(self):
        logger.info("Running test_handle_online_status_change")
        # Initial state: online, API key OK
        self.mock_check_internet.return_value = True
        self.module.update_status_and_ui() # Set initial state
        self.assertTrue(self.module.submit_button.isEnabled())

        # Simulate going offline
        self.mock_main_window.online_status_changed.emit(False)
        # The slot should call update_status_and_ui, which uses mock_check_internet.
        # We need to ensure mock_check_internet reflects the new reality for the check within update_status_and_ui
        self.mock_check_internet.return_value = False 
        self.module.handle_online_status_change(False) # Explicitly call for clarity, though signal should do it

        self.assertFalse(self.module.submit_button.isEnabled())
        self.assertIn("Offline", self.module.status_info_label.text())

        # Simulate going back online
        self.mock_main_window.online_status_changed.emit(True)
        self.mock_check_internet.return_value = True
        self.module.handle_online_status_change(True)

        self.assertTrue(self.module.submit_button.isEnabled())
        self.assertIn("Online", self.module.status_info_label.text())
        logger.info("Finished test_handle_online_status_change")

    def test_on_submit_prompt_empty(self):
        logger.info("Running test_on_submit_prompt_empty")
        self.module.prompt_input.setText("")
        self.module._on_submit_prompt()
        self.mock_qmessagebox.warning.assert_called_once()
        self.mock_get_ai_response.assert_not_called()
        logger.info("Finished test_on_submit_prompt_empty")

    def test_on_submit_prompt_offline(self):
        logger.info("Running test_on_submit_prompt_offline")
        self.module.prompt_input.setText("Test prompt")
        self.mock_check_internet.return_value = False
        self.module.update_status_and_ui() # Update internal state to offline

        self.module._on_submit_prompt()
        
        self.mock_qmessagebox.critical.assert_called_once()
        self.assertIn("offline", self.mock_qmessagebox.critical.call_args[0][1].lower()) # Ensure lowercase comparison
        self.mock_get_ai_response.assert_not_called()
        logger.info("Finished test_on_submit_prompt_offline")

    def test_on_submit_prompt_no_api_key(self):
        logger.info("Running test_on_submit_prompt_no_api_key")
        self.module.prompt_input.setText("Test prompt")
        self.mock_check_internet.return_value = True
        
        with patch('app.gui.modules.ai_assistant_module.ai_client', None):
            self.module.update_status_and_ui() # Update internal state to API key missing
            self.module._on_submit_prompt()
        
        self.mock_qmessagebox.critical.assert_called_once()
        self.assertIn("api key error", self.mock_qmessagebox.critical.call_args[0][1].lower())
        self.mock_get_ai_response.assert_not_called()
        logger.info("Finished test_on_submit_prompt_no_api_key")

    @patch('app.gui.modules.ai_assistant_module.AIWorker')      # Outer patch, provides mock_AIWorker_cls
    @patch('app.gui.modules.ai_assistant_module.QThread')       # Inner patch, provides mock_QThread_cls
    def test_on_submit_prompt_success_starts_worker(self, mock_QThread_cls, mock_AIWorker_cls): # Corrected parameter names
        logger.info("Running test_on_submit_prompt_success_starts_worker")
        self.module.prompt_input.setText("Valid prompt")
        self.mock_check_internet.return_value = True
        # API key is OK by default mock from setUp
        self.module.update_status_and_ui()

        # Create mock instances that the mocked constructors will return
        mock_worker_instance = MagicMock(spec=AIWorker)  # Mock instance of AIWorker
        mock_thread_instance = MagicMock(spec=QThread)  # Mock instance of QThread

        # Configure the mocked class constructors to return these mock instances
        mock_AIWorker_cls.return_value = mock_worker_instance
        mock_QThread_cls.return_value = mock_thread_instance
        
        self.module._on_submit_prompt() # Calls QThread() and AIWorker(...)

        # Assert that the class constructors were called as expected
        mock_AIWorker_cls.assert_called_once_with("Valid prompt", model="gpt-3.5-turbo")
        mock_QThread_cls.assert_called_once_with() # QThread constructor is called with no args

        # Assert that methods were called on the *instances*
        mock_worker_instance.moveToThread.assert_called_once_with(mock_thread_instance)
        mock_thread_instance.start.assert_called_once()

        # Check for the specific span tag that QTextEdit generates for italic text
        self.assertIn('<span style=" font-style:italic;">Thinking...</span>', self.module.response_area.toHtml())
        self.assertFalse(self.module.submit_button.isEnabled())
        self.assertFalse(self.module.prompt_input.isEnabled())
        logger.info("Finished test_on_submit_prompt_success_starts_worker")

    # AIWorker tests
    def test_ai_worker_success(self):
        logger.info("Running test_ai_worker_success")
        self.mock_get_ai_response.return_value = "Successful AI response"
        worker = AIWorker("test prompt")
        
        mock_response_handler = MagicMock()
        mock_error_handler = MagicMock()
        mock_finished_handler = MagicMock()

        worker.response_ready.connect(mock_response_handler)
        worker.error_occurred.connect(mock_error_handler)
        worker.finished.connect(mock_finished_handler)

        worker.run()

        mock_response_handler.assert_called_once_with("Successful AI response")
        mock_error_handler.assert_not_called()
        mock_finished_handler.assert_called_once()
        logger.info("Finished test_ai_worker_success")

    def test_ai_worker_api_error_response(self):
        logger.info("Running test_ai_worker_api_error_response")
        self.mock_get_ai_response.return_value = "Error: Some API problem"
        worker = AIWorker("test prompt for error")

        mock_response_handler = MagicMock()
        mock_error_handler = MagicMock()
        mock_finished_handler = MagicMock()

        worker.response_ready.connect(mock_response_handler)
        worker.error_occurred.connect(mock_error_handler)
        worker.finished.connect(mock_finished_handler)

        worker.run()

        mock_error_handler.assert_called_once_with("Error: Some API problem")
        mock_response_handler.assert_not_called()
        mock_finished_handler.assert_called_once()
        logger.info("Finished test_ai_worker_api_error_response")
        
    def test_ai_worker_exception_in_get_ai_response(self):
        logger.info("Running test_ai_worker_exception_in_get_ai_response")
        self.mock_get_ai_response.side_effect = Exception("Unexpected worker error")
        worker = AIWorker("test prompt for exception")

        mock_response_handler = MagicMock()
        mock_error_handler = MagicMock()
        mock_finished_handler = MagicMock()

        worker.response_ready.connect(mock_response_handler)
        worker.error_occurred.connect(mock_error_handler)
        worker.finished.connect(mock_finished_handler)

        worker.run()

        mock_error_handler.assert_called_once_with("An unexpected error occurred in the AI worker: Unexpected worker error")
        mock_response_handler.assert_not_called()
        mock_finished_handler.assert_called_once()
        logger.info("Finished test_ai_worker_exception_in_get_ai_response")


if __name__ == '__main__':
    unittest.main()
