#!/usr/bin/env python3
"""
Minimal CLI chat app demonstrating any-llm library capabilities.
Shows ease of switching between models and feature differences.
"""

import os
import sys
import json
from typing import Optional, List, Dict, Any, Callable
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from any_llm import completion, AnyLLM

# Load environment variables
load_dotenv()

console = Console()


# Available models with their capabilities
MODELS = {
    "1": {
        "name": "gpt-4o",
        "provider": "openai",
        "supports_tools": True,
        "supports_streaming": True,
        "notes": "Fast, capable general-purpose model"
    },
    "2": {
        "name": "gpt-4o-mini",
        "provider": "openai",
        "supports_tools": True,
        "supports_streaming": True,
        "notes": "Smaller, faster, cheaper version"
    },
    "3": {
        "name": "claude-3-5-sonnet-20241022",
        "provider": "anthropic",
        "supports_tools": True,
        "supports_streaming": True,
        "notes": "Excellent reasoning and code generation"
    },
    "4": {
        "name": "claude-3-5-haiku-20241022",
        "provider": "anthropic",
        "supports_tools": True,
        "supports_streaming": True,
        "notes": "Fast and efficient"
    },
    "5": {
        "name": "mistral-small-latest",
        "provider": "mistral",
        "supports_tools": True,
        "supports_streaming": True,
        "notes": "Fast and efficient European model"
    },
    "6": {
        "name": "mistral-large-latest",
        "provider": "mistral",
        "supports_tools": True,
        "supports_streaming": True,
        "notes": "Strong European alternative"
    },
}


def get_weather(location: str, unit: str = "fahrenheit") -> str:
    """Get the current weather for a location.

    Args:
        location: The city and state, e.g., San Francisco, CA
        unit: The temperature unit (celsius or fahrenheit)

    Returns:
        Weather information as a string
    """
    # Mock response
    temp = 72 if unit == "fahrenheit" else 22
    return f"The weather in {location} is {temp}°{unit[0].upper()} and sunny."


def calculate(expression: str) -> str:
    """Perform a mathematical calculation.

    Args:
        expression: The mathematical expression to evaluate, e.g., '2 + 2' or '10 * 5'

    Returns:
        The calculation result
    """
    try:
        # Simple eval for demo purposes (not for production!)
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"


# Available tools as Python functions
TOOLS = [get_weather, calculate]


def display_models():
    """Display available models in a table."""
    table = Table(title="Available Models", show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Model", style="green")
    table.add_column("Provider", style="yellow")
    table.add_column("Tools", justify="center")
    table.add_column("Stream", justify="center")
    table.add_column("Notes")

    for key, model in MODELS.items():
        table.add_row(
            key,
            model["name"],
            model["provider"].capitalize(),
            "✓" if model["supports_tools"] else "✗",
            "✓" if model["supports_streaming"] else "✗",
            model["notes"]
        )

    console.print(table)


def chat_with_model(model_name: str, provider: str, use_tools: bool = False, use_streaming: bool = True):
    """Start an interactive chat session with the specified model."""
    messages = []

    model_info = next((m for m in MODELS.values() if m["name"] == model_name), None)
    if not model_info:
        console.print(f"[red]Error: Unknown model {model_name}[/red]")
        return

    # Display model info
    console.print(Panel(
        f"[bold green]{model_info['name']}[/bold green]\n"
        f"Provider: {model_info['provider']}\n"
        f"Tools: {'Enabled' if use_tools and model_info['supports_tools'] else 'Disabled'}\n"
        f"Streaming: {'Enabled' if use_streaming and model_info['supports_streaming'] else 'Disabled'}",
        title="Current Model",
        border_style="blue"
    ))

    console.print("\n[dim]Commands: /switch (change model), /tools (toggle tools), /clear (clear history), /quit (exit)[/dim]\n")

    while True:
        try:
            # Get user input
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")

            # Handle commands
            if user_input.lower() == "/quit":
                break
            elif user_input.lower() == "/switch":
                return "switch"
            elif user_input.lower() == "/tools":
                use_tools = not use_tools
                console.print(f"[yellow]Tools {'enabled' if use_tools else 'disabled'}[/yellow]")
                continue
            elif user_input.lower() == "/clear":
                messages = []
                console.print("[yellow]Conversation history cleared[/yellow]")
                continue
            elif not user_input.strip():
                continue

            # Add user message
            messages.append({"role": "user", "content": user_input})

            # Prepare API call parameters
            kwargs = {
                "model": model_name,
                "provider": provider,
                "messages": messages,
            }

            if use_tools and model_info["supports_tools"]:
                kwargs["tools"] = TOOLS

            # Make API call
            console.print("\n[bold green]Assistant[/bold green]")

            if use_streaming and model_info["supports_streaming"]:
                # Streaming response
                full_response = ""
                tool_calls_data = []
                current_tool_call = None

                try:
                    for chunk in completion(**kwargs, stream=True):
                        if hasattr(chunk.choices[0], 'delta'):
                            delta = chunk.choices[0].delta

                            # Handle content
                            if hasattr(delta, 'content') and delta.content:
                                console.print(delta.content, end="")
                                full_response += delta.content

                            # Handle tool calls (streaming)
                            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                                for tc in delta.tool_calls:
                                    if tc.index is not None:
                                        # Start or continue a tool call
                                        while len(tool_calls_data) <= tc.index:
                                            tool_calls_data.append({
                                                "id": None,
                                                "type": "function",
                                                "function": {"name": "", "arguments": ""}
                                            })

                                        if tc.id:
                                            tool_calls_data[tc.index]["id"] = tc.id
                                        if tc.function:
                                            if tc.function.name:
                                                tool_calls_data[tc.index]["function"]["name"] = tc.function.name
                                            if tc.function.arguments:
                                                tool_calls_data[tc.index]["function"]["arguments"] += tc.function.arguments

                    console.print()  # New line after streaming

                    # Process tool calls if any
                    if tool_calls_data and any(tc.get("id") for tc in tool_calls_data):
                        # Create proper tool call objects for the message
                        from types import SimpleNamespace

                        tool_call_objects = []
                        for tc_data in tool_calls_data:
                            if tc_data.get("id"):
                                tc_obj = SimpleNamespace(
                                    id=tc_data["id"],
                                    type=tc_data["type"],
                                    function=SimpleNamespace(
                                        name=tc_data["function"]["name"],
                                        arguments=tc_data["function"]["arguments"]
                                    )
                                )
                                tool_call_objects.append(tc_obj)

                        messages.append({
                            "role": "assistant",
                            "content": full_response or None,
                            "tool_calls": tool_call_objects
                        })

                        console.print("\n[yellow]🔧 Executing tools...[/yellow]")

                        # Execute each tool
                        for tool_call in tool_call_objects:
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)

                            console.print(f"[dim]→ {tool_name}({tool_args})[/dim]")

                            # Find and execute the tool
                            result = None
                            for tool_func in TOOLS:
                                if tool_func.__name__ == tool_name:
                                    result = tool_func(**tool_args)
                                    break

                            if result is None:
                                result = f"Error: Tool {tool_name} not found"

                            # Add tool response
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result
                            })

                        # Get final response with tool results
                        console.print("\n[bold green]Assistant (with tool results)[/bold green]")
                        final_response = ""

                        for chunk in completion(
                            model=model_name,
                            provider=provider,
                            messages=messages,
                            stream=True
                        ):
                            if hasattr(chunk.choices[0], 'delta'):
                                delta = chunk.choices[0].delta
                                if hasattr(delta, 'content') and delta.content:
                                    console.print(delta.content, end="")
                                    final_response += delta.content

                        console.print()
                        messages.append({"role": "assistant", "content": final_response})
                    else:
                        # No tool calls, just add the response
                        if full_response:
                            messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    console.print(f"\n[red]Error: {str(e)}[/red]")
                    console.print(f"[dim]This might be due to missing API keys or model limitations.[/dim]")
                    messages.pop()  # Remove the user message if there was an error

            else:
                # Non-streaming response
                try:
                    response = completion(**kwargs)
                    assistant_message = response.choices[0].message

                    if hasattr(assistant_message, 'content') and assistant_message.content:
                        console.print(assistant_message.content)

                    # Handle tool calls
                    if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                        console.print("\n[yellow]🔧 Executing tools...[/yellow]")

                        messages.append({
                            "role": "assistant",
                            "content": assistant_message.content,
                            "tool_calls": assistant_message.tool_calls
                        })

                        for tool_call in assistant_message.tool_calls:
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)

                            console.print(f"[dim]→ {tool_name}({tool_args})[/dim]")

                            # Find and execute the tool
                            result = None
                            for tool_func in TOOLS:
                                if tool_func.__name__ == tool_name:
                                    result = tool_func(**tool_args)
                                    break

                            if result is None:
                                result = f"Error: Tool {tool_name} not found"

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result
                            })

                        # Get final response
                        final = completion(model=model_name, provider=provider, messages=messages)
                        final_content = final.choices[0].message.content
                        console.print(f"\n[bold green]Assistant (with tool results)[/bold green]\n{final_content}")
                        messages.append({"role": "assistant", "content": final_content})
                    else:
                        # No tool calls
                        messages.append({"role": "assistant", "content": assistant_message.content})

                except Exception as e:
                    console.print(f"[red]Error: {str(e)}[/red]")
                    console.print(f"[dim]This might be due to missing API keys or model limitations.[/dim]")
                    messages.pop()

        except KeyboardInterrupt:
            console.print("\n[yellow]Chat interrupted[/yellow]")
            break
        except EOFError:
            break

    return None


def main():
    """Main application entry point."""
    console.print(Panel.fit(
        "[bold blue]any-llm POC - Minimal CLI Chat[/bold blue]\n"
        "Test model switching and feature differences",
        border_style="blue"
    ))

    # Check for API keys
    api_keys = {
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "Mistral": os.getenv("MISTRAL_API_KEY"),
    }

    console.print("\n[bold]API Key Status:[/bold]")
    for provider, key in api_keys.items():
        status = "✓" if key else "✗"
        color = "green" if key else "red"
        console.print(f"  [{color}]{status} {provider}[/{color}]")

    console.print()

    while True:
        # Show models and let user select
        display_models()

        choice = Prompt.ask(
            "\n[bold]Select a model (1-6) or 'q' to quit[/bold]",
            choices=list(MODELS.keys()) + ["q"],
            default="1"
        )

        if choice == "q":
            console.print("[yellow]Goodbye![/yellow]")
            break

        model_info = MODELS[choice]
        current_model = model_info["name"]
        current_provider = model_info["provider"]

        # Ask about tools
        use_tools = Prompt.ask(
            "\n[bold]Enable tool calling?[/bold]",
            choices=["y", "n"],
            default="y"
        ) == "y"

        # Start chat
        result = chat_with_model(current_model, current_provider, use_tools=use_tools)

        if result != "switch":
            break


if __name__ == "__main__":
    main()
