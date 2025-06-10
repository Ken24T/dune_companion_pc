\
# filepath: c:\\repos\\dune_companion_pc\\app\\utils\\ai_utils.py
"""
Utilities for interacting with AI services, primarily OpenAI.
"""
import openai
import os # Ensure os is imported

from app.utils.logger import get_logger

logger = get_logger(__name__)

# User-provided API key for personal use.
# For broader applications, using environment variables is recommended for security.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client with the API key
# This should be done once, ideally when the module is loaded.
client = None # Initialize client to None
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY) # Assign to the globally defined client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
        # client remains None
else:
    logger.warning("OpenAI API key is not set. AI features will not be available.")
    # client remains None

def get_ai_response(prompt_text: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Gets a response from the OpenAI Chat API.

    Args:
        prompt_text: The user's prompt.
        model: The OpenAI model to use (e.g., "gpt-3.5-turbo", "gpt-4").

    Returns:
        The AI's response as a string, or an error message.
    """
    if not client: # Check the globally defined client
        return "Error: OpenAI client not initialized. API key may be missing or invalid."

    try:
        logger.info(f"Sending prompt to OpenAI API (model: {model}): '{prompt_text[:50]}...'")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for the game Dune: Awakening. Provide concise and relevant information."},
                {"role": "user", "content": prompt_text}
            ]
        )
        
        if not response.choices:
            logger.warning("No response choices received from OpenAI API.")
            return "Error: No response choices received from the AI."

        content = response.choices[0].message.content
        
        if content is None or not content.strip():
            logger.warning("Received an empty message content from OpenAI API.")
            return "Error: Received an empty response from the AI."
            
        ai_message = content.strip()
        logger.info(f"Received response from OpenAI API: '{ai_message[:50]}...'")
        return ai_message
    except openai.APIConnectionError as e:
        logger.error(f"OpenAI API connection error: {e}")
        return f"Error: Could not connect to OpenAI. Please check your internet connection. Details: {e}"
    except openai.RateLimitError as e:
        logger.error(f"OpenAI API rate limit exceeded: {e}")
        return f"Error: OpenAI API rate limit exceeded. Please try again later. Details: {e}"
    except openai.AuthenticationError as e:
        logger.error(f"OpenAI API authentication error: {e}")
        return f"Error: OpenAI API authentication failed. Please check your API key. Details: {e}"
    # Ensure openai.APIError is caught before the generic Exception
    except openai.APIError as e: # Catch other API-related errors
        logger.error(f"OpenAI API error: {e}")
        return f"Error: An OpenAI API error occurred. Details: {e}"
    except Exception as e:
        logger.error(f"An unexpected error occurred while calling OpenAI API: {e}", exc_info=True)
        return f"Error: An unexpected error occurred. Details: {e}"

if __name__ == '__main__':
    # This is for testing the function directly.
    # Ensure your OPENAI_API_KEY is set above or as an environment variable.
    if not openai.api_key: # Check if the key was set for the openai module
        logger.warning("API key not configured for direct test run for the openai module.")
    if not client: # Also check if our client initialized
        logger.warning("OpenAI client not initialized for direct test run.")
    else:
        test_prompts = [
            "What are the main resources needed for crafting a thumper?",
            "Give me a brief overview of House Atreides in Dune.",
            "Suggest a good starting strategy for a new player in Dune: Awakening focusing on exploration."
        ]
        for prompt in test_prompts:
            print(f"\\nTesting prompt: {prompt}") # Using \\n for newline in f-string for print
            ai_answer = get_ai_response(prompt)
            print(f"AI Answer: {ai_answer}")
