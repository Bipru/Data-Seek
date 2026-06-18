"""
chart_generator.py - DataSeekAI Chart Generation Module

This module processes structured insights from the AI engine and converts them
into chart-ready data formats compatible with Chart.js frontend library.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChartType(str, Enum):
    """Enum for supported chart types"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    TABLE = "table"
    NONE = "none"


# Supported chart types for validation
SUPPORTED_CHART_TYPES = {chart_type.value for chart_type in ChartType}


def validate_ai_response(ai_response: Dict[str, Any]) -> bool:
    """
    Validate the structure and content of AI response.
    
    Args:
        ai_response (dict): Response from AI engine
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Check if response is a dictionary
    if not isinstance(ai_response, dict):
        logger.error(f"AI response is not a dictionary: {type(ai_response)}")
        return False
    
    # Check required fields
    required_fields = ["text", "chart_type", "labels", "values"]
    for field in required_fields:
        if field not in ai_response:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate text field
    if not isinstance(ai_response["text"], str):
        logger.error("Text field must be a string")
        return False
    
    # Validate chart_type
    chart_type = ai_response["chart_type"]
    if chart_type not in SUPPORTED_CHART_TYPES:
        logger.error(f"Unsupported chart type: {chart_type}")
        return False
    
    # For chart types other than 'none', validate labels and values
    if chart_type == ChartType.SCATTER.value:
        scatter_data = ai_response.get("scatter_data", [])
        if not isinstance(scatter_data, list) or len(scatter_data) == 0:
            logger.error("Scatter chart requires scatter_data as a non-empty list of {x, y} objects")
            return False
        for i, pt in enumerate(scatter_data):
            if not isinstance(pt, dict) or "x" not in pt or "y" not in pt:
                logger.error(f"scatter_data[{i}] must have 'x' and 'y' keys")
                return False
        return True

    elif chart_type != ChartType.NONE.value:
        labels = ai_response["labels"]
        values = ai_response["values"]
        
        # Check if labels and values are lists
        if not isinstance(labels, list) or not isinstance(values, list):
            logger.error("Labels and values must be lists")
            return False
        
        # Check if they have the same length
        if len(labels) != len(values):
            logger.error(f"Labels and values length mismatch: {len(labels)} vs {len(values)}")
            return False
        
        # Check if they are non-empty for pie charts (pie charts need at least one data point)
        if chart_type == ChartType.PIE.value and len(labels) == 0:
            logger.error("Pie chart requires at least one data point")
            return False
        
        # Validate value types (should be numeric)
        for i, value in enumerate(values):
            if not isinstance(value, (int, float)):
                logger.error(f"Value at index {i} is not numeric: {type(value)}")
                return False
    
    return True


def prepare_chart_data(ai_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare chart data in Chart.js compatible format.
    
    Args:
        ai_response (dict): Validated AI response
    
    Returns:
        dict: Chart.js compatible data structure
    """
    chart_type = ai_response["chart_type"]
    labels = ai_response.get("labels", [])
    values = ai_response.get("values", [])
    
    # Base chart data structure for Chart.js
    chart_data = {
        "type": chart_type,
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": "DataSeekAI Insights",
                    "data": values,
                    "backgroundColor": generate_colors(len(values), chart_type),
                    "borderColor": generate_border_colors(len(values), chart_type),
                    "borderWidth": 1
                }
            ]
        }
    }
    
    # Add chart-specific configurations
    if chart_type == ChartType.BAR.value:
        chart_data["options"] = {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top"
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True
                }
            }
        }
    
    elif chart_type == ChartType.LINE.value:
        chart_data["options"] = {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top"
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True
                }
            },
            "elements": {
                "line": {
                    "tension": 0.4  # Slight curve for smoother lines
                }
            }
        }
    
    elif chart_type == ChartType.PIE.value:
        chart_data["options"] = {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "right"
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) { return `${context.label}: ${context.raw}`; }"
                    }
                }
            }
        }
    
    return chart_data


def prepare_scatter_data(ai_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare scatter plot data in Chart.js compatible format.

    Args:
        ai_response (dict): Validated AI response with scatter_data [{x, y}, ...]

    Returns:
        dict: Chart.js compatible scatter data structure
    """
    scatter_points = ai_response.get("scatter_data", [])
    x_label = ai_response.get("x_label", "X")
    y_label = ai_response.get("y_label", "Y")

    chart_data = {
        "type": "scatter",
        "data": {
            "datasets": [
                {
                    "label": f"{x_label} vs {y_label}",
                    "data": scatter_points,  # [{x: .., y: ..}, ...]
                    "backgroundColor": "rgba(99, 179, 237, 0.7)",
                    "borderColor": "rgba(99, 179, 237, 1)",
                    "pointRadius": 6,
                    "pointHoverRadius": 9,
                }
            ]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": True, "position": "top"}
            },
            "scales": {
                "x": {"title": {"display": True, "text": x_label}},
                "y": {"beginAtZero": False, "title": {"display": True, "text": y_label}}
            }
        }
    }
    return chart_data


def prepare_table_data(ai_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare data for table display.
    
    Args:
        ai_response (dict): Validated AI response
    
    Returns:
        dict: Table-formatted data
    """
    labels = ai_response.get("labels", [])
    values = ai_response.get("values", [])
    
    # Create table rows from labels and values
    rows = []
    for label, value in zip(labels, values):
        rows.append([label, value])
    
    table_data = {
        "headers": ["Category", "Value"],
        "rows": rows
    }
    
    return table_data


def generate_colors(count: int, chart_type: str) -> List[str]:
    """
    Generate colors for chart datasets.
    
    Args:
        count (int): Number of colors needed
        chart_type (str): Type of chart (affects color scheme)
    
    Returns:
        list: List of color strings in rgba format
    """
    # Professional color palette
    colors = [
        "rgba(54, 162, 235, 0.8)",   # Blue
        "rgba(255, 99, 132, 0.8)",    # Pink
        "rgba(75, 192, 192, 0.8)",    # Teal
        "rgba(255, 159, 64, 0.8)",    # Orange
        "rgba(153, 102, 255, 0.8)",   # Purple
        "rgba(255, 205, 86, 0.8)",    # Yellow
        "rgba(201, 203, 207, 0.8)",   # Grey
        "rgba(46, 134, 222, 0.8)",    # Dark Blue
        "rgba(231, 76, 60, 0.8)",     # Red
        "rgba(26, 188, 156, 0.8)",    # Green
    ]
    
    # Repeat colors if needed
    if count > len(colors):
        colors = colors * (count // len(colors) + 1)
    
    # For line charts, we typically want a single color
    if chart_type == ChartType.LINE.value:
        return ["rgba(54, 162, 235, 0.8)"]
    
    return colors[:count]


def generate_border_colors(count: int, chart_type: str) -> List[str]:
    """
    Generate border colors for chart datasets.
    
    Args:
        count (int): Number of colors needed
        chart_type (str): Type of chart
    
    Returns:
        list: List of border color strings
    """
    # Darker versions of the fill colors for borders
    border_colors = [
        "rgba(54, 162, 235, 1)",    # Blue
        "rgba(255, 99, 132, 1)",     # Pink
        "rgba(75, 192, 192, 1)",     # Teal
        "rgba(255, 159, 64, 1)",     # Orange
        "rgba(153, 102, 255, 1)",    # Purple
        "rgba(255, 205, 86, 1)",     # Yellow
        "rgba(201, 203, 207, 1)",    # Grey
        "rgba(46, 134, 222, 1)",     # Dark Blue
        "rgba(231, 76, 60, 1)",      # Red
        "rgba(26, 188, 156, 1)",     # Green
    ]
    
    if count > len(border_colors):
        border_colors = border_colors * (count // len(border_colors) + 1)
    
    # For line charts, use a single border color
    if chart_type == ChartType.LINE.value:
        return ["rgba(54, 162, 235, 1)"]
    
    return border_colors[:count]


def generate_chart_data(ai_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to generate chart-ready data from AI response.
    
    Args:
        ai_response (dict): Response from AI engine in format:
            {
                "text": "Insight explanation",
                "chart_type": "bar",
                "labels": ["A", "B", "C"],
                "values": [10, 20, 30]
            }
    
    Returns:
        dict: Formatted response for frontend with chart data
    """
    try:
        # Validate input
        if not validate_ai_response(ai_response):
            logger.warning("Invalid AI response, returning fallback")
            return {
                "text": ai_response.get("text", "Invalid data for chart generation"),
                "chart": None,
                "table": None
            }
        
        # Extract data
        text = ai_response["text"]
        chart_type = ai_response["chart_type"]
        
        # Handle 'none' chart type
        if chart_type == ChartType.NONE.value:
            return {
                "text": text,
                "chart": None,
                "table": None
            }
        
        # Handle table type
        if chart_type == ChartType.TABLE.value:
            table_data = prepare_table_data(ai_response)
            return {
                "text": text,
                "chart": None,
                "table": table_data
            }
        
        # Handle chart types (bar, line, pie, scatter)
        if chart_type == ChartType.SCATTER.value:
            chart_data = prepare_scatter_data(ai_response)
        else:
            chart_data = prepare_chart_data(ai_response)

        return {
            "text": text,
            "chart": chart_data,
            "table": None
        }
    
    except Exception as e:
        logger.error(f"Error generating chart data: {str(e)}", exc_info=True)
        return {
            "text": "Chart generation failed due to an internal error.",
            "chart": None,
            "table": None
        }


def generate_multiple_charts(ai_responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate chart data for multiple AI responses.
    
    Args:
        ai_responses (list): List of AI response dictionaries
    
    Returns:
        list: List of formatted chart responses
    """
    return [generate_chart_data(response) for response in ai_responses]


def format_for_streaming(ai_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format chart data for streaming responses (partial updates).
    
    Args:
        ai_response (dict): AI response dictionary
    
    Returns:
        dict: Formatted response suitable for streaming
    """
    result = generate_chart_data(ai_response)
    
    # Add metadata for streaming
    result["metadata"] = {
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "version": "1.0"
    }
    
    return result


def validate_chart_compatibility(ai_response: Dict[str, Any], frontend_capabilities: Dict[str, bool]) -> Dict[str, Any]:
    """
    Validate if the generated chart is compatible with frontend capabilities.
    
    Args:
        ai_response (dict): AI response dictionary
        frontend_capabilities (dict): Dictionary indicating supported features
    
    Returns:
        dict: Chart data with compatibility flags
    """
    result = generate_chart_data(ai_response)
    
    if result.get("chart"):
        chart_type = result["chart"]["type"]
        
        # Check if chart type is supported by frontend
        if not frontend_capabilities.get(chart_type, False):
            # Fallback to table if chart type not supported
            result["chart"] = None
            result["table"] = prepare_table_data(ai_response)
            result["text"] += " (Displayed as table due to frontend limitations)"
    
    return result


# Example usage and testing
def test_chart_generator():
    """Test function to verify chart generator works correctly"""
    
    # Test cases
    test_cases = [
        {
            "name": "Valid bar chart",
            "input": {
                "text": "Sales by region show North leading with $18,000",
                "chart_type": "bar",
                "labels": ["North", "South", "East", "West"],
                "values": [18000, 15000, 12000, 16000]
            }
        },
        {
            "name": "Valid pie chart",
            "input": {
                "text": "Market share distribution",
                "chart_type": "pie",
                "labels": ["Product A", "Product B", "Product C"],
                "values": [45, 30, 25]
            }
        },
        {
            "name": "Valid line chart",
            "input": {
                "text": "Monthly revenue trend shows steady growth",
                "chart_type": "line",
                "labels": ["Jan", "Feb", "Mar", "Apr"],
                "values": [10000, 12000, 11500, 14000]
            }
        },
        {
            "name": "Table format",
            "input": {
                "text": "Top products by units sold",
                "chart_type": "table",
                "labels": ["Product A", "Product B", "Product C"],
                "values": [150, 120, 90]
            }
        },
        {
            "name": "No chart",
            "input": {
                "text": "The document discusses quarterly financial performance.",
                "chart_type": "none",
                "labels": [],
                "values": []
            }
        },
        {
            "name": "Invalid data (mismatched lengths)",
            "input": {
                "text": "This should trigger fallback",
                "chart_type": "bar",
                "labels": ["A", "B"],
                "values": [10, 20, 30]
            }
        }
    ]
    
    print("Testing Chart Generator Module\n" + "="*50)
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print("-" * 30)
        result = generate_chart_data(test["input"])
        
        print(f"Text: {result['text'][:50]}...")
        if result.get("chart"):
            print(f"Chart Type: {result['chart']['type']}")
            print(f"Data Points: {len(result['chart']['data']['labels'])}")
        elif result.get("table"):
            print(f"Table Headers: {result['table']['headers']}")
            print(f"Table Rows: {len(result['table']['rows'])}")
        else:
            print("No visualization (text only)")
    
    return True


if __name__ == "__main__":
    # Run tests if script is executed directly
    test_chart_generator()