"""
ai_engine.py - DataSeekAI AI Integration Module

This module handles all interactions with Google's Gemini API to generate
insights and chart recommendations from user queries and uploaded file data.
"""

import os
import json
import logging
import re
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Gemini library
try:
    import google.generativeai as genai
except ImportError:
    logger.error("google-generativeai library not installed")
    genai = None

# Constants
DEFAULT_MODEL = "gemini-2.5-flash"
MAX_TEXT_LENGTH = 5000  # Maximum characters to send for text documents
MAX_PREVIEW_ROWS = 10    # Maximum rows to include in context


def initialize_model(api_key: Optional[str] = None, model_name: str = DEFAULT_MODEL) -> Optional[Any]:
    """
    Initialize the Gemini model with API key.
    
    Args:
        api_key (str, optional): Gemini API key. If not provided, reads from environment.
        model_name (str): Name of the Gemini model to use.
    
    Returns:
        GenerativeModel: Initialized model instance or None if initialization fails.
    """
    # Check if library is available
    if genai is None:
        logger.error("google-generativeai library is not installed")
        return None
    
    # Get API key
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("GEMINI_API_KEY not found in environment variables")
        return None
    
    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize model
        model = genai.GenerativeModel(model_name)
        logger.info(f"Successfully initialized Gemini model: {model_name}")
        return model
    
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model: {str(e)}")
        return None


def generate_prompt(user_query: str, parsed_file_data: Dict[str, Any]) -> str:
    """
    Generate a detailed prompt for the AI based on user query and file data.
    
    Args:
        user_query (str): The user's question
        parsed_file_data (dict): Output from file_parser.py
    
    Returns:
        str: Formatted prompt for Gemini
    """
    # Extract file type and data
    file_type = parsed_file_data.get("type", "unknown")
    
    # Base system prompt
    system_prompt = """You are DataSeekAI, an expert Business Intelligence assistant. Your role is to analyze data and provide clear, actionable insights with appropriate visualizations.

When responding:
1. Analyze the user's question carefully in the context of the provided data
2. For tabular data, identify relevant columns and patterns
3. Recommend the most effective chart type (bar, line, pie, scatter, table, or none)
4. Provide specific, data-backed insights
5. If the data doesn't support the query, explain what's available instead

Respond ONLY with valid JSON in this exact format:
{
    "text": "Your detailed insight here...",
    "chart_type": "bar|line|pie|scatter|table|none",
    "labels": ["label1", "label2", ...],
    "values": [value1, value2, ...],
    "scatter_data": [{"x": x1, "y": y1}, {"x": x2, "y": y2}, ...]
}

For "scatter" chart type, populate "scatter_data" with {x, y} objects and leave "labels"/"values" as empty arrays.
For all other chart types, populate "labels" and "values" and leave "scatter_data" as an empty array.
For "none" chart type, provide empty arrays for all data fields.
"""
    
    # Build context based on file type
    if file_type == "table":
        # Tabular data context
        columns = parsed_file_data.get("columns", [])
        preview = parsed_file_data.get("data_preview", [])
        row_count = parsed_file_data.get("row_count", 0)
        numeric_columns = parsed_file_data.get("numeric_columns", [])
        
        # Format preview data nicely
        preview_text = json.dumps(preview[:MAX_PREVIEW_ROWS], indent=2)
        
        context = f"""
FILE TYPE: Tabular Data (CSV/Excel)

DATA OVERVIEW:
- Total rows: {row_count}
- Columns: {', '.join(columns)}
- Numeric columns: {', '.join(numeric_columns) if numeric_columns else 'None'}

DATA PREVIEW (first {min(MAX_PREVIEW_ROWS, len(preview))} rows):
{preview_text}

USER QUERY: {user_query}

Based on this tabular data, provide insights and chart recommendations. Consider:
- Which columns are relevant to the query?
- What aggregations (sum, average, count) might be needed?
- What chart type would best visualize the answer?
- What patterns or trends do you observe?
"""
    
    elif file_type == "text":
        # Text document context
        content = parsed_file_data.get("content", "")
        content_preview = content[:MAX_TEXT_LENGTH]
        if len(content) > MAX_TEXT_LENGTH:
            content_preview += "... [content truncated]"
        
        metadata = parsed_file_data.get("metadata", {})
        
        context = f"""
FILE TYPE: Text Document (PDF/DOCX/PPTX)

DOCUMENT METADATA:
{json.dumps(metadata, indent=2)}

DOCUMENT CONTENT PREVIEW:
{content_preview}

USER QUERY: {user_query}

Based on this document content, provide insights and analysis. Consider:
- What are the key points related to the query?
- Can you summarize the relevant sections?
- If the query asks for specific information, extract it.
- For text documents, chart_type should typically be "none" unless the data suggests visualization.
"""
    
    else:
        # Error or unknown type
        error_message = parsed_file_data.get("message", "Unknown file type")
        context = f"""
FILE TYPE: Unknown or Error
STATUS: {error_message}

USER QUERY: {user_query}

Please acknowledge that the file couldn't be properly parsed and suggest uploading a supported file format (CSV, Excel, PDF, DOCX, PPTX).
"""
    
    # Combine system prompt with context
    full_prompt = f"{system_prompt}\n\n{context}"
    
    return full_prompt


def parse_ai_response(response_text: str) -> Dict[str, Any]:
    """
    Parse the AI response and extract JSON data safely.
    
    Args:
        response_text (str): Raw response from Gemini
    
    Returns:
        dict: Parsed response with text, chart_type, labels, values
    """
    # Default fallback response
    fallback = {
        "text": "The system could not generate a structured insight.",
        "chart_type": "none",
        "labels": [],
        "values": []
    }
    
    try:
        # Clean the response text
        cleaned_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        # Parse JSON
        response_json = json.loads(cleaned_text)
        
        # Validate required fields
        if "text" not in response_json:
            response_json["text"] = fallback["text"]
        
        if "chart_type" not in response_json:
            response_json["chart_type"] = "none"
        
        if "labels" not in response_json:
            response_json["labels"] = []
        
        if "values" not in response_json:
            response_json["values"] = []
        
        # Validate chart_type
        valid_chart_types = ["bar", "line", "pie", "scatter", "table", "none"]
        if response_json["chart_type"] not in valid_chart_types:
            response_json["chart_type"] = "none"
        
        # Ensure labels and values are lists
        if not isinstance(response_json["labels"], list):
            response_json["labels"] = []
        
        if not isinstance(response_json["values"], list):
            response_json["values"] = []
        
        # For chart types other than none, ensure labels and values are synchronized
        if response_json["chart_type"] == "scatter":
            # scatter uses scatter_data: [{x, y}, ...]
            scatter_data = response_json.get("scatter_data", [])
            if not isinstance(scatter_data, list) or len(scatter_data) == 0:
                response_json["chart_type"] = "none"
                response_json["scatter_data"] = []
            else:
                response_json["scatter_data"] = scatter_data
                response_json["labels"] = []
                response_json["values"] = []
        elif response_json["chart_type"] != "none":
            min_length = min(len(response_json["labels"]), len(response_json["values"]))
            if min_length == 0:
                # If no valid data, downgrade to none
                response_json["chart_type"] = "none"
                response_json["labels"] = []
                response_json["values"] = []
            else:
                # Trim to equal lengths
                response_json["labels"] = response_json["labels"][:min_length]
                response_json["values"] = response_json["values"][:min_length]
        
        return response_json
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        logger.debug(f"Raw response: {response_text}")
        
        # Attempt to extract JSON from text using regex as fallback
        json_pattern = r'\{[^{}]*\}'
        matches = re.findall(json_pattern, response_text)
        
        for match in matches:
            try:
                response_json = json.loads(match)
                logger.info("Successfully extracted JSON using regex fallback")
                return response_json
            except:
                continue
        
        return fallback
    
    except Exception as e:
        logger.error(f"Unexpected error parsing AI response: {e}")
        return fallback


def generate_insight(
    user_query: str,
    parsed_file_data: Dict[str, Any],
    model: Optional[Any] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main function to generate insights using Gemini API.
    
    Args:
        user_query (str): The user's question
        parsed_file_data (dict): Output from file_parser.py
        model: Optional pre-initialized Gemini model
        api_key: Optional API key (will use environment if not provided)
    
    Returns:
        dict: Structured insight with text, chart_type, labels, values
    """
    # Validate input
    if not user_query or not user_query.strip():
        return {
            "text": "Please provide a valid question.",
            "chart_type": "none",
            "labels": [],
            "values": []
        }
    
    # Check if parsed_file_data contains an error
    if parsed_file_data.get("type") == "error":
        return {
            "text": f"File parsing error: {parsed_file_data.get('message', 'Unknown error')}",
            "chart_type": "none",
            "labels": [],
            "values": []
        }
    
    # Initialize model if not provided
    if model is None:
        model = initialize_model(api_key)
        if model is None:
            return {
                "text": "AI service is not available. Please check your API key configuration.",
                "chart_type": "none",
                "labels": [],
                "values": []
            }
    
    try:
        # Generate prompt
        prompt = generate_prompt(user_query, parsed_file_data)
        
        # Log prompt for debugging (truncated)
        logger.debug(f"Sending prompt to Gemini (first 200 chars): {prompt[:200]}...")
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Check if response is valid
        if not response or not response.text:
            logger.error("Empty response from Gemini")
            return {
                "text": "The AI service returned an empty response. Please try again.",
                "chart_type": "none",
                "labels": [],
                "values": []
            }
        
        # Parse response
        insight = parse_ai_response(response.text)
        
        # Add metadata about the analysis
        if insight["chart_type"] != "none":
            insight["text"] = f"📊 {insight['text']}"
        
        return insight
    
    except Exception as e:
        logger.error(f"Error generating insight: {str(e)}", exc_info=True)
        return {
            "text": f"An error occurred while generating insights: {str(e)}",
            "chart_type": "none",
            "labels": [],
            "values": []
        }


def generate_insight_with_retry(
    user_query: str,
    parsed_file_data: Dict[str, Any],
    max_retries: int = 3,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate insight with retry logic for transient failures.
    
    Args:
        user_query (str): The user's question
        parsed_file_data (dict): Output from file_parser.py
        max_retries (int): Maximum number of retry attempts
        api_key: Optional API key
    
    Returns:
        dict: Structured insight
    """
    model = initialize_model(api_key)
    if model is None:
        return {
            "text": "Failed to initialize AI model. Please check your configuration.",
            "chart_type": "none",
            "labels": [],
            "values": []
        }
    
    for attempt in range(max_retries):
        try:
            result = generate_insight(user_query, parsed_file_data, model)
            
            # Check if result is valid (not the error fallback)
            if result["text"] != "The system could not generate a structured insight.":
                return result
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
        
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                return {
                    "text": f"Failed after {max_retries} attempts. Last error: {str(e)}",
                    "chart_type": "none",
                    "labels": [],
                    "values": []
                }
    
    return {
        "text": "Unable to generate insight after multiple attempts.",
        "chart_type": "none",
        "labels": [],
        "values": []
    }


# Optional: Function to test the AI engine
def test_ai_engine():
    """Test function to verify AI engine works with sample data"""
    
    # Sample tabular data
    sample_table = {
        "type": "table",
        "columns": ["Product", "Sales", "Region", "Month"],
        "data_preview": [
            {"Product": "Laptop", "Sales": 45000, "Region": "North", "Month": "Jan"},
            {"Product": "Laptop", "Sales": 52000, "Region": "South", "Month": "Jan"},
            {"Product": "Mouse", "Sales": 12000, "Region": "North", "Month": "Jan"},
            {"Product": "Mouse", "Sales": 15000, "Region": "South", "Month": "Jan"},
            {"Product": "Keyboard", "Sales": 18000, "Region": "North", "Month": "Jan"}
        ],
        "row_count": 5,
        "numeric_columns": ["Sales"]
    }
    
    # Sample query
    query = "What are the total sales by product?"
    
    # Generate insight
    result = generate_insight(query, sample_table)
    
    print("AI Engine Test Result:")
    print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    # Run test if script is executed directly
    print("Testing DataSeekAI AI Engine...")
    test_ai_engine()