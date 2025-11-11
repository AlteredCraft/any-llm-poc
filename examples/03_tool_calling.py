#!/usr/bin/env python3
"""
Tool calling demonstration: Test tool/function calling across models.
Shows how any-llm handles tool calling consistently.
"""

import os
import json
from dotenv import load_dotenv
from any_llm import completion
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

# Models that support tool calling
MODELS = [
    ("openai", "gpt-4o-mini"),
    ("anthropic", "claude-3-5-haiku-20241022"),
    ("mistral", "mistral-small-latest"),
]

PROMPT = "What's the weather like in San Francisco? Should I bring an umbrella?"


# Define tools as Python functions
def get_current_temperature(location: str, unit: str) -> str:
    """Get the current temperature for a specific location.

    Args:
        location: The city and state, e.g., San Francisco, CA
        unit: The temperature unit to use (celsius or fahrenheit)

    Returns:
        Temperature information as JSON string
    """
    # Mock response
    return json.dumps({
        "temperature": 68 if unit == "fahrenheit" else 20,
        "unit": unit,
        "location": location
    })


def get_rain_probability(location: str) -> str:
    """Get the probability of rain for a specific location.

    Args:
        location: The city and state, e.g., San Francisco, CA

    Returns:
        Rain probability information as JSON string
    """
    # Mock response
    return json.dumps({
        "probability": 15,
        "description": "Low chance of rain",
        "location": location
    })


# List of tool functions
TOOLS = [get_current_temperature, get_rain_probability]


def test_tool_calling(provider: str, model: str):
    """Test tool calling with a single model."""
    console.print(f"\n[bold cyan]Testing tool calling: {provider}/{model}[/bold cyan]")

    messages = [{"role": "user", "content": PROMPT}]

    try:
        # First request with tools
        response = completion(
            model=model,
            provider=provider,
            messages=messages,
            tools=TOOLS  # Pass Python functions directly!
        )

        assistant_message = response.choices[0].message

        # Check for tool calls
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            console.print(f"[green]✓ Model used {len(assistant_message.tool_calls)} tool(s)[/green]")

            # Add assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": assistant_message.tool_calls
            })

            # Execute tools and add results
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                console.print(f"\n[dim]Tool call:[/dim]")
                console.print(f"  [yellow]Function:[/yellow] {tool_name}")
                console.print(f"  [yellow]Arguments:[/yellow] {tool_args}")

                # Find and execute the tool
                result = None
                for tool_func in TOOLS:
                    if tool_func.__name__ == tool_name:
                        result = tool_func(**tool_args)
                        break

                if result is None:
                    result = json.dumps({"error": f"Tool {tool_name} not found"})

                console.print(f"  [yellow]Result:[/yellow] {result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

            # Get final response with tool results
            final_response = completion(
                model=model,
                provider=provider,
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
        console.print(f"[red]Error with {provider}/{model}: {str(e)}[/red]")
        console.print(f"[dim]Make sure you have the required API key set ({provider.upper()}_API_KEY).[/dim]")


def main():
    console.print(Panel.fit(
        "[bold blue]Tool Calling Demonstration[/bold blue]\n"
        "Test function/tool calling across providers using any-llm",
        border_style="blue"
    ))

    console.print(f"\n[bold]Prompt:[/bold] {PROMPT}\n")
    console.print("[bold]Available tools (Python functions):[/bold]")
    console.print("  • get_current_temperature(location, unit)")
    console.print("  • get_rain_probability(location)")

    for provider, model in MODELS:
        test_tool_calling(provider, model)

    console.print("\n[bold green]✓ Tool calling test complete![/bold green]")
    console.print("[dim]any-llm lets you pass Python functions directly as tools![/dim]")
    console.print("[dim]The library automatically converts them to the provider's format.[/dim]")


if __name__ == "__main__":
    main()
