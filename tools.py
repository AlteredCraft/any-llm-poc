import json
import logging
from typing import Callable

logger = logging.getLogger(__name__)


# Tool functions for any-llm
def get_weather(location: str, unit: str = "F") -> str:
    """Get weather information for a location.

    Args:
        location: The city or location to get weather for
        unit: Temperature unit, either 'C' or 'F'

    Returns:
        str: Weather information for the location
    """
    # Pseudo implementation - returns mock weather data
    temp = 75 if unit == "F" else 24
    return f"Weather in {location} is sunny and {temp}{unit}!"


def divide(dividend: float, divisor: float) -> float:
    """Divide two numbers.

    Args:
        dividend: The number to be divided
        divisor: The number to divide by

    Returns:
        float: The result of dividend / divisor

    Raises:
        ValueError: If divisor is zero
    """
    if divisor == 0:
        raise ValueError("Cannot divide by zero")
    return dividend / divisor


# List of available tools
AVAILABLE_TOOLS = [
    {
        "name": "get_weather",
        "description": "Get weather information for a location",
        "parameters": {
            "location": {"type": "string", "description": "The city or location to get weather for"},
            "unit": {"type": "string", "description": "Temperature unit, either 'C' or 'F'", "default": "F"}
        }
    },
    {
        "name": "divide",
        "description": "Divide two numbers",
        "parameters": {
            "dividend": {"type": "number", "description": "The number to be divided"},
            "divisor": {"type": "number", "description": "The number to divide by"}
        }
    }
]

# Mapping of tool names to callable functions
TOOL_FUNCTIONS: dict[str, Callable] = {
    "get_weather": get_weather,
    "divide": divide,
}


def execute_tool_call(tool_call) -> dict:
    """Execute a single tool call and return the result"""
    try:
        # Extract tool name and arguments from function attribute
        tool_name = tool_call.function.name
        # Parse arguments - they come as a JSON string
        arguments = json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments

        logger.info(f"Executing tool: {tool_name} with arguments: {arguments}")

        # Get the function
        if tool_name not in TOOL_FUNCTIONS:
            error_msg = f"Unknown tool: {tool_name}"
            logger.error(error_msg)
            return {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": json.dumps({"error": error_msg})
            }

        # Execute the function
        func = TOOL_FUNCTIONS[tool_name]
        result = func(**arguments)

        logger.info(f"Tool {tool_name} executed successfully: {result}")

        # Return formatted tool result
        # Wrap result in JSON object for provider compatibility
        if isinstance(result, dict):
            content = json.dumps(result)
        else:
            content = json.dumps({"result": result})

        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_name,
            "content": content
        }
    except Exception as e:
        error_msg = f"Error executing tool {getattr(tool_call.function, 'name', 'unknown')}: {str(e)}"
        logger.error(error_msg)
        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": getattr(tool_call.function, 'name', 'unknown'),
            "content": json.dumps({"error": str(e)})
        }
