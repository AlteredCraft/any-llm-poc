#!/usr/bin/env python3
"""
Tool calling demonstration: Test tool/function calling across models.
Shows how any-llm handles tool calling consistently.
"""

import os
import json
from dotenv import load_dotenv
from any_llm import LiteLLMClient
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

load_dotenv()
console = Console()

# Models that support tool calling
MODELS = [
    "gpt-4o-mini",
    "claude-3-5-haiku-20241022",
]

# Define tools
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_temperature",
            "description": "Get the current temperature for a specific location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g., San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The temperature unit to use"
                    }
                },
                "required": ["location", "unit"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_rain_probability",
            "description": "Get the probability of rain for a specific location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g., San Francisco, CA"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

PROMPT = "What's the weather like in San Francisco? Should I bring an umbrella?"


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Mock tool execution."""
    if tool_name == "get_current_temperature":
        return json.dumps({
            "temperature": 68,
            "unit": arguments.get("unit", "fahrenheit")
        })
    elif tool_name == "get_rain_probability":
        return json.dumps({
            "probability": 15,
            "description": "Low chance of rain"
        })
    return json.dumps({"error": "Unknown tool"})


def test_tool_calling(client: LiteLLMClient, model: str):
    """Test tool calling with a single model."""
    console.print(f"\n[bold cyan]Testing tool calling: {model}[/bold cyan]")

    messages = [{"role": "user", "content": PROMPT}]

    try:
        # First request
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS
        )

        assistant_message = response.choices[0].message

        # Check for tool calls
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            console.print(f"[green]✓ Model used {len(assistant_message.tool_calls)} tool(s)[/green]")

            # Add assistant message with tool calls
            messages.append({
                "role": "assistant",
                "tool_calls": assistant_message.tool_calls
            })

            # Execute tools and add results
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                console.print(f"\n[dim]Tool call:[/dim]")
                console.print(f"  [yellow]Function:[/yellow] {tool_name}")
                console.print(f"  [yellow]Arguments:[/yellow] {tool_args}")

                result = execute_tool(tool_name, tool_args)
                console.print(f"  [yellow]Result:[/yellow] {result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

            # Get final response
            final_response = client.chat.completions.create(
                model=model,
                messages=messages
            )

            final_content = final_response.choices[0].message.content
            console.print(f"\n[bold]Final response:[/bold]")
            console.print(Panel(final_content, border_style="green"))

        else:
            # No tool calls made
            console.print("[yellow]! Model did not use tools[/yellow]")
            if hasattr(assistant_message, 'content') and assistant_message.content:
                console.print(Panel(assistant_message.content, border_style="yellow"))

    except Exception as e:
        console.print(f"[red]Error with {model}: {str(e)}[/red]")


def main():
    console.print(Panel.fit(
        "[bold blue]Tool Calling Demonstration[/bold blue]\n"
        "Test function/tool calling across providers",
        border_style="blue"
    ))

    console.print(f"\n[bold]Prompt:[/bold] {PROMPT}\n")
    console.print("[bold]Available tools:[/bold]")
    console.print("  • get_current_temperature")
    console.print("  • get_rain_probability")

    client = LiteLLMClient()

    for model in MODELS:
        test_tool_calling(client, model)

    console.print("\n[bold green]✓ Tool calling test complete![/bold green]")
    console.print("[dim]any-llm provides consistent tool calling across OpenAI, Anthropic, and other providers.[/dim]")


if __name__ == "__main__":
    main()
