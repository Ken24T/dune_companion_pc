\
# filepath: c:\\repos\\dune_companion_pc\\app\\utils\\ai_utils.py
"""
Utilities for interacting with AI services, primarily OpenAI.
"""
import openai
import os # Ensure os is imported
import json # Add json for parsing tool arguments
import httpx # Add httpx for making HTTP requests
from bs4 import BeautifulSoup # Add BeautifulSoup for HTML parsing

from openai.types.chat import ( # Import specific types for better type hinting
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
    ChatCompletionMessageToolCallParam
)
# Import the specific Function type for ChatCompletionMessageToolCallParam
from openai.types.chat.chat_completion_message_tool_call_param import Function as ToolCallParamFunction

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

def fetch_webpage_content(url: str) -> str:
    """
    Fetches and extracts textual content from a webpage.

    Args:
        url: The URL of the webpage.

    Returns:
        The extracted text content or an error message.
    """
    try:
        logger.info(f"Fetching content from URL: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Use a timeout to prevent hanging indefinitely
        response = httpx.get(url, headers=headers, follow_redirects=True, timeout=10.0)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # Check if content type is HTML or XML, otherwise it might be a binary file
        content_type = response.headers.get("content-type", "").lower()
        if not ("html" in content_type or "xml" in content_type):
            logger.warning(f"Content type of {url} is {content_type}, not HTML/XML. Skipping parsing.")
            return f"Error: Content type is {content_type}. Only HTML/XML pages can be processed."

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Get text, using '\\n' as a separator between text elements
        text = soup.get_text(separator='\\n')

        # Break into lines and remove leading/trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text_content = '\\n'.join(chunk for chunk in chunks if chunk)
        
        if not text_content:
            logger.warning(f"No text content extracted from {url}")
            return "Error: No text content could be extracted from the webpage."

        logger.info(f"Successfully extracted content from {url} (length: {len(text_content)})")
        # Limit content length to avoid overly large payloads to OpenAI
        MAX_CONTENT_LENGTH = 15000 
        if len(text_content) > MAX_CONTENT_LENGTH:
            logger.info(f"Content from {url} truncated to {MAX_CONTENT_LENGTH} characters.")
            return text_content[:MAX_CONTENT_LENGTH] + "... (content truncated)"
        return text_content

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred while fetching {url}: {e}")
        return f"Error: Could not fetch webpage. Status code: {e.response.status_code}"
    except httpx.RequestError as e:
        logger.error(f"Request error occurred while fetching {url}: {e}")
        return f"Error: Could not fetch webpage. Request failed: {e}"
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching webpage content from {url}: {e}", exc_info=True)
        return f"Error: An unexpected error occurred while processing the webpage. Details: {e}"

def get_ai_response(prompt_text: str, model: str = "gpt-4") -> str:
    """
    Gets a response from the OpenAI Chat API, potentially using tools like web browsing.

    Args:
        prompt_text: The user's prompt.
        model: The OpenAI model to use (e.g., "gpt-4").

    Returns:
        The AI's response as a string, or an error message.
    """
    if not client:
        return "Error: OpenAI client not initialized. API key may be missing or invalid."

    # Correctly typed messages list
    messages: list[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(role="system", content="You are a helpful assistant for the game Dune: Awakening. Provide concise and relevant information. You have access to a web browsing tool."),
        ChatCompletionUserMessageParam(role="user", content=prompt_text)
    ]
    
    # Correctly typed tools list
    tools: list[ChatCompletionToolParam] = [
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
    ]

    try:
        logger.info(f"Sending prompt to OpenAI API (model: {model}) with tools: '{prompt_text[:50]}...'")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto", 
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            logger.info(f"AI requested to use tools: {tool_calls}")
            
            tool_call_params: list[ChatCompletionMessageToolCallParam] = []
            for tc in tool_calls:
                tool_call_params.append(ChatCompletionMessageToolCallParam(
                    id=tc.id,
                    function=ToolCallParamFunction(name=tc.function.name, arguments=tc.function.arguments),
                    type='function'
                ))

            assistant_message_with_tool_call = ChatCompletionAssistantMessageParam(
                role="assistant", 
                content=response_message.content, 
                tool_calls=tool_call_params
            )
            messages.append(assistant_message_with_tool_call)

            for tool_call in tool_calls: # Iterate through all tool calls if multiple are made
                if tool_call.function.name == "fetch_webpage_content":
                    try:
                        tool_function_args = json.loads(tool_call.function.arguments)
                        url_to_fetch = tool_function_args.get("url")
                        
                        if not url_to_fetch:
                            logger.error("AI requested fetch_webpage_content without a URL.")
                            # Append a tool message indicating error for this specific tool call
                            messages.append(ChatCompletionToolMessageParam(
                                tool_call_id=tool_call.id,
                                role="tool",
                                name="fetch_webpage_content",
                                content="Error: Tool call for web browsing was missing the URL."
                            ))
                            continue # Move to the next tool call if any

                        logger.info(f"Calling fetch_webpage_content for URL: {url_to_fetch}")
                        tool_response_content = fetch_webpage_content(url=url_to_fetch)
                        
                        messages.append(ChatCompletionToolMessageParam(
                            tool_call_id=tool_call.id,
                            role="tool",
                            name="fetch_webpage_content",
                            content=tool_response_content,
                        ))

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse arguments for tool call {tool_call.function.name}: {e}")
                        messages.append(ChatCompletionToolMessageParam(
                            tool_call_id=tool_call.id,
                            role="tool",
                            name="fetch_webpage_content",
                            content=f"Error: Could not parse arguments for AI tool call: {e}"
                        ))
                        continue # Move to the next tool call
                    except Exception as e:
                        logger.error(f"Error during tool execution ({tool_call.function.name}): {e}", exc_info=True)
                        messages.append(ChatCompletionToolMessageParam(
                            tool_call_id=tool_call.id,
                            role="tool",
                            name="fetch_webpage_content",
                            content=f"Error: An unexpected error occurred while executing AI tool {tool_call.function.name}: {e}"
                        ))
                        continue # Move to the next tool call
                else:
                    logger.warning(f"AI requested an unknown tool: {tool_call.function.name}")
                    messages.append(ChatCompletionToolMessageParam(
                        tool_call_id=tool_call.id,
                        role="tool",
                        name=tool_call.function.name, # Use the name AI provided
                        content=f"Error: Unknown tool '{tool_call.function.name}' requested."
                    ))
            
            logger.info("Sending tool response(s) back to OpenAI API...")
            second_response = client.chat.completions.create(
                model=model,
                messages=messages, # messages list now includes assistant's tool request and all tool responses
            )
            
            final_content = second_response.choices[0].message.content
            if final_content is None or not final_content.strip():
                logger.warning("Received an empty message content from OpenAI API after tool call(s).")
                return "Error: Received an empty response from the AI after tool use."
            
            ai_message = final_content.strip()
            logger.info(f"Received final response from OpenAI API after tool call(s): '{ai_message[:50]}...'")
            return ai_message
        
        # Fallback if no tool_calls were made or if logic somehow skipped returning after tool_calls
        content = response_message.content
        if content is None or not content.strip():
            logger.warning("Received an empty message content from OpenAI API (no tool call or unhandled path).")
            return "Error: Received an empty response from the AI."
            
        ai_message = content.strip()
        logger.info(f"Received response from OpenAI API (no tool call executed or unhandled path): '{ai_message[:50]}...'")
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
        # Test fetching a specific page and printing its content
        test_url = "https://www.duneawakening.com/"
        print(f"\\nFetching content from: {test_url}")
        fetched_content = fetch_webpage_content(test_url)
        print(f"--- Fetched Content Start ---\\n{fetched_content}\\n--- Fetched Content End ---")

        # Then test the AI response with a prompt that should use this type of info
        prompt_for_release_date = f"Based on the previously fetched content from {test_url}, what is the official release date for Dune: Awakening? If it's not there, say so."
        print(f"\\nTesting prompt: {prompt_for_release_date}")
        ai_answer = get_ai_response(prompt_for_release_date) # The AI will fetch again, this is for simplicity here
        print(f"AI Answer: {ai_answer}")

        # Original test prompts (optional, can be commented out if focusing on web fetch)
        # test_prompts = [
        #     "What are the main resources needed for crafting a thumper?",
        #     "Give me a brief overview of House Atreides in Dune.",
        #     "Suggest a good starting strategy for a new player in Dune: Awakening focusing on exploration.",
        #     "Summarize the main page of the official Dune: Awakening website, duneawakening.com."
        # ]
        # for prompt in test_prompts:
        #     print(f"\\nTesting prompt: {prompt}")
        #     ai_answer = get_ai_response(prompt)
        #     print(f"AI Answer: {ai_answer}")
