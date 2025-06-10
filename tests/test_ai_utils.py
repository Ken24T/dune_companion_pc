\
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Temporarily adjust path to import from app.utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module and the function to test
import app.utils.ai_utils # Import the module itself to access/patch its globals
from app.utils.ai_utils import get_ai_response
from app.utils.logger import get_logger

# Ensure a logger is available for the module if it's used during testing
logger = get_logger(__name__)

class TestAIUtils(unittest.TestCase):

    def setUp(self):
        # Store original os.environ to restore it later
        self.original_environ = os.environ.copy()
        # Patch 'app.utils.ai_utils.client' for most tests to isolate from actual client init
        self.client_patcher = patch('app.utils.ai_utils.client')
        self.mock_ai_client = self.client_patcher.start()
        
        # For tests that specifically check client initialization (e.g., no API key),
        # we will stop this patcher and use a different approach.

    def tearDown(self):
        # Stop any patchers started in setUp or individual tests
        self.client_patcher.stop()
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_environ)
        # Ensure the global client in ai_utils is reset to its original state after tests
        # This might involve re-importing or a specific re-initialization if the module supports it.
        # For now, we rely on tests properly mocking/patching.
        # A more robust way would be to have a re-init function in ai_utils or reload the module.
        # For simplicity here, we'll assume patching in tests is sufficient.
        # A bit of a hack; ideally, ai_utils.py would have a reinit function
        import importlib
        importlib.reload(app.utils.ai_utils)


    # No longer need _patch_env_var and _unpatch_env_var as we manage os.environ directly
    # or use patch.dict for specific tests.

    # mock_ai_client is now passed from setUp's patcher
    def test_get_ai_response_success(self):
        logger.info("Running test_get_ai_response_success")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Test AI response"
        self.mock_ai_client.chat.completions.create.return_value = mock_response

        prompt = "Test prompt"
        response = get_ai_response(prompt)
        
        self.assertEqual(response, "Test AI response")
        self.mock_ai_client.chat.completions.create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for the game Dune: Awakening. Provide concise and relevant information."},
                {"role": "user", "content": prompt}
            ]
        )
        logger.info("Finished test_get_ai_response_success")

    def test_get_ai_response_api_error(self):
        logger.info("Running test_get_ai_response_api_error")
        from openai import APIError 
        self.mock_ai_client.chat.completions.create.side_effect = APIError("Simulated API Error", request=MagicMock(), body=None) # Replaced None with MagicMock()

        prompt = "Test prompt for API error"
        response = get_ai_response(prompt)
        
        self.assertTrue(response.startswith("Error: An OpenAI API error occurred. Details: "))
        logger.info("Finished test_get_ai_response_api_error")

    def test_get_ai_response_network_error(self):
        logger.info("Running test_get_ai_response_network_error")
        from openai import APIConnectionError
        self.mock_ai_client.chat.completions.create.side_effect = APIConnectionError(request=MagicMock())

        prompt = "Test prompt for network error"
        response = get_ai_response(prompt)
        
        self.assertTrue(response.startswith("Error: Could not connect to OpenAI."))
        logger.info("Finished test_get_ai_response_network_error")

    # This test needs to specifically stop the default client_patcher
    # and control the client initialization process.
    def test_get_ai_response_no_api_key(self):
        logger.info("Running test_get_ai_response_no_api_key")
        self.client_patcher.stop() # Stop the default patch

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
            # Patch the constructor where it's imported and used
            with patch('openai.OpenAI') as mock_openai_constructor:
                # Simulate that client initialization fails or results in None
                mock_openai_constructor.return_value = None 
                
                # Reload ai_utils to make it re-evaluate the client based on the new (empty) API key
                import importlib
                importlib.reload(app.utils.ai_utils)
                
                # At this point, app.utils.ai_utils.client should be None
                self.assertIsNone(app.utils.ai_utils.client, "Client should be None when API key is missing")

                response = get_ai_response("Test prompt with no API key")
                self.assertEqual(response, "Error: OpenAI client not initialized. API key may be missing or invalid.")
        
        # Restart the client_patcher for subsequent tests that rely on it.
        # This is important because test execution order is not guaranteed.
        self.client_patcher.start()
        logger.info("Finished test_get_ai_response_no_api_key")


    def test_get_ai_response_empty_response_content(self):
        logger.info("Running test_get_ai_response_empty_response_content")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = None
        self.mock_ai_client.chat.completions.create.return_value = mock_response

        prompt = "Test prompt for empty content"
        response = get_ai_response(prompt)
        
        self.assertEqual(response, "Error: Received an empty response from the AI.") # Adjusted expected error
        logger.info("Finished test_get_ai_response_empty_response_content")

    def test_get_ai_response_no_choices(self):
        logger.info("Running test_get_ai_response_no_choices")
        mock_response = MagicMock()
        mock_response.choices = []
        self.mock_ai_client.chat.completions.create.return_value = mock_response

        prompt = "Test prompt for no choices"
        response = get_ai_response(prompt)
        
        self.assertEqual(response, "Error: No response choices received from the AI.")
        logger.info("Finished test_get_ai_response_no_choices")

if __name__ == '__main__':
    unittest.main()
