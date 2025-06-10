\
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Temporarily adjust path to import from app.utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module and the function to test
import app.utils.ai_utils # Import the module itself to access/patch its globals
from app.utils.ai_utils import get_ai_response, fetch_webpage_content # Add fetch_webpage_content
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
        
        # Patch httpx.get for fetch_webpage_content tests
        self.httpx_patcher = patch('httpx.get')
        self.mock_httpx_get = self.httpx_patcher.start()

    def tearDown(self):
        # Stop any patchers started in setUp or individual tests
        self.client_patcher.stop()
        self.httpx_patcher.stop() # Stop httpx_patcher
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_environ)
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
        mock_response.choices[0].message.tool_calls = None # Ensure no tool calls for this test
        self.mock_ai_client.chat.completions.create.return_value = mock_response

        prompt = "Test prompt"
        response = get_ai_response(prompt)
        
        self.assertEqual(response, "Test AI response")
        self.mock_ai_client.chat.completions.create.assert_called_once_with(
            model="gpt-4", # Updated to gpt-4
            messages=[
                {"role": "system", "content": "You are a helpful assistant for the game Dune: Awakening. Provide concise and relevant information. You have access to a web browsing tool."},
                {"role": "user", "content": prompt}
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "fetch_webpage_content",
                        "description": "Fetches the textual content of a given URL. Use this to answer questions that require up-to-date information or accessing specific websites.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "The URL of the webpage to fetch.",
                                }
                            },
                            "required": ["url"],
                        },
                    },
                }
            ],
            tool_choice="auto"
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
        mock_response.choices[0].message.tool_calls = None # Ensure no tool_calls
        self.mock_ai_client.chat.completions.create.return_value = mock_response

        prompt = "Test prompt for empty content"
        response = get_ai_response(prompt)
        
        self.assertEqual(response, "Error: Received an empty response from the AI.")
        logger.info("Finished test_get_ai_response_empty_response_content")

    def test_get_ai_response_no_choices(self):
        logger.info("Running test_get_ai_response_no_choices")
        mock_response = MagicMock()
        mock_response.choices = [] # No choices
        # No need to set tool_calls if there are no choices
        self.mock_ai_client.chat.completions.create.return_value = mock_response

        prompt = "Test prompt for no choices"
        # This scenario will likely raise an IndexError before checking tool_calls or content.
        # The exact error message might depend on how robust the error handling is for this case.
        # Based on current get_ai_response, it would be an IndexError.
        # Let's adjust the test to expect a generic error or a specific one if the code handles it.
        # For now, assuming it might lead to a generic error due to unexpected structure.
        # Update: The code has try-except for IndexError when accessing response.choices[0]
        # However, the current structure of get_ai_response would raise IndexError before specific handling.
        # Let's assume the function should handle it gracefully.
        # If response.choices is empty, response.choices[0] will raise IndexError.
        # The main try-except block in get_ai_response should catch this.
        response = get_ai_response(prompt)
        self.assertTrue(response.startswith("Error: An unexpected error occurred. Details: list index out of range"))
        logger.info("Finished test_get_ai_response_no_choices")

    # New tests for fetch_webpage_content
    def test_fetch_webpage_content_success(self):
        logger.info("Running test_fetch_webpage_content_success")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.content = b"<html><head><title>Test Page</title></head><body><p>Hello World</p></body></html>"
        self.mock_httpx_get.return_value = mock_response

        content = fetch_webpage_content("http://example.com")
        self.assertEqual(content, "Test Page\\nHello World")
        self.mock_httpx_get.assert_called_once_with("http://example.com", follow_redirects=True, timeout=10.0)
        logger.info("Finished test_fetch_webpage_content_success")

    def test_fetch_webpage_content_http_error(self):
        logger.info("Running test_fetch_webpage_content_http_error")
        import httpx # Import httpx for the exception
        mock_response = MagicMock()
        mock_response.status_code = 404
        self.mock_httpx_get.side_effect = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)

        content = fetch_webpage_content("http://example.com/notfound")
        self.assertEqual(content, "Error: Could not fetch webpage. Status code: 404")
        logger.info("Finished test_fetch_webpage_content_http_error")

    def test_fetch_webpage_content_request_error(self):
        logger.info("Running test_fetch_webpage_content_request_error")
        import httpx # Import httpx for the exception
        self.mock_httpx_get.side_effect = httpx.RequestError("Connection Failed", request=MagicMock())

        content = fetch_webpage_content("http://example.com/failed")
        self.assertEqual(content, "Error: Could not fetch webpage. Request failed: Connection Failed")
        logger.info("Finished test_fetch_webpage_content_request_error")

    def test_fetch_webpage_content_non_html(self):
        logger.info("Running test_fetch_webpage_content_non_html")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.content = b'{"key": "value"}'
        self.mock_httpx_get.return_value = mock_response

        content = fetch_webpage_content("http://example.com/data.json")
        self.assertEqual(content, "Error: Content type is application/json. Only HTML/XML pages can be processed.")
        logger.info("Finished test_fetch_webpage_content_non_html")

    def test_fetch_webpage_content_empty_content(self):
        logger.info("Running test_fetch_webpage_content_empty_content")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.content = b"<html><body></body></html>"
        self.mock_httpx_get.return_value = mock_response

        content = fetch_webpage_content("http://example.com/empty")
        self.assertEqual(content, "Error: No text content could be extracted from the webpage.")
        logger.info("Finished test_fetch_webpage_content_empty_content")

    # Test for get_ai_response with tool call
    def test_get_ai_response_with_tool_call_success(self):
        logger.info("Running test_get_ai_response_with_tool_call_success")
        # Mock first AI call (requests tool use)
        mock_initial_response = MagicMock()
        mock_initial_response.choices = [MagicMock()]
        mock_initial_message = MagicMock()
        mock_initial_message.content = None # AI asks to use a tool
        mock_tool_call = MagicMock()
        mock_tool_call.id = "tool_call_123"
        mock_tool_call.type = "function"
        mock_tool_call.function = MagicMock()
        mock_tool_call.function.name = "fetch_webpage_content"
        mock_tool_call.function.arguments = '{"url": "http://example.com"}'
        mock_initial_message.tool_calls = [mock_tool_call]
        mock_initial_response.choices[0].message = mock_initial_message

        # Mock webpage fetch
        self.mock_httpx_get.return_value = MagicMock(
            status_code=200, 
            headers={"content-type": "text/html"}, 
            content=b"<html><body><p>Webpage content</p></body></html>"
        )

        # Mock second AI call (processes tool result)
        mock_final_response = MagicMock()
        mock_final_response.choices = [MagicMock()]
        mock_final_message = MagicMock()
        mock_final_message.content = "Final AI response after browsing."
        mock_final_response.choices[0].message = mock_final_message

        self.mock_ai_client.chat.completions.create.side_effect = [
            mock_initial_response, 
            mock_final_response
        ]

        prompt = "Summarize example.com"
        response = get_ai_response(prompt)

        self.assertEqual(response, "Final AI response after browsing.")
        self.assertEqual(self.mock_ai_client.chat.completions.create.call_count, 2)
        # Add more assertions here to check the arguments of the calls if necessary
        first_call_args = self.mock_ai_client.chat.completions.create.call_args_list[0]
        second_call_args = self.mock_ai_client.chat.completions.create.call_args_list[1]

        self.assertEqual(first_call_args[1]['model'], "gpt-4")
        self.assertIn("fetch_webpage_content", str(first_call_args[1]['tools']))

        self.assertEqual(second_call_args[1]['model'], "gpt-4")
        messages = second_call_args[1]['messages']
        self.assertEqual(messages[-1]['role'], "tool")
        self.assertEqual(messages[-1]['tool_call_id'], "tool_call_123")
        self.assertEqual(messages[-1]['name'], "fetch_webpage_content")
        self.assertIn("Webpage content", messages[-1]['content'])

        logger.info("Finished test_get_ai_response_with_tool_call_success")

if __name__ == '__main__':
    unittest.main()
