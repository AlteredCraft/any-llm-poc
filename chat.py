#!/usr/bin/env python3
"""
Minimal CLI chat app demonstrating any-llm library capabilities.
Shows ease of switching between models and feature differences.
"""

import os
import sys
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.table import Table
from any_llm import LiteLLMClient

# Load environment variables
load_dotenv()

console = Console()


# Available models with their capabilities
MODELS = {
    "1": {
        "name": "gpt-4o",
        "provider": "OpenAI",
        "supports_tools": True,
        "supports_streaming": True,
        "supports_thinking": False,
        "notes": "Fast, capable general-purpose model"
    },
    "2": {
        "name": "gpt-4o-mini",
        "provider": "OpenAI",
        "supports_tools": True,
        "supports_streaming": True,
        "supports_thinking": False,
        "notes": "Smaller, faster, cheaper version"
    },
    "3": {
        "name": "claude-3-5-sonnet-20241022",
        "provider": "Anthropic",
        "supports_tools": True,
        "supports_streaming": True,
        "supports_thinking": False,
        "notes": "Excellent reasoning and code generation"
    },
    "4": {
        "name": "claude-3-5-haiku-20241022",
        "provider": "Anthropic",
        "supports_tools": True,
        "supports_streaming": True,
        "supports_thinking": False,
        "notes": "Fast and efficient"
    },
    "5": {
        "name": "mistral-large-latest",
        "provider": "Mistral",
        "supports_tools": True,
        "supports_streaming": True,
        "supports_thinking": False,
        "notes": "Strong European alternative"
    },
    "6": {
        "name": "gemini-2.0-flash-exp",
        "provider": "Google",
        "supports_tools": True,
        "supports_streaming": True,
        "supports_thinking": True,
        "notes": "Fast multimodal model with thinking"
    },
}


# Example tools for demonstrating tool calling
EXAMPLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
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
                        "description": "The temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a mathematical calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate, e.g., '2 + 2' or '10 * 5'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute a tool call and return the result."""
    if tool_name == "get_weather":
        location = arguments.get("location", "Unknown")
        unit = arguments.get("unit", "fahrenheit")
        # Mock response
        return f"The weather in {location} is 72°{unit[0].upper()} and sunny."

    elif tool_name == "calculate":
        expression = arguments.get("expression", "")
        try:
            # Simple eval for demo purposes (not for production!)
            result = eval(expression, {"__builtins__": {}}, {})
            return f"Result: {result}"
        except Exception as e:
            return f"Error calculating: {str(e)}"

    return f"Unknown tool: {tool_name}"


def display_models():
    """Display available models in a table."""
    table = Table(title="Available Models", show_header=True, header_style="bold magenta")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Model", style="green")
    table.add_column("Provider", style="yellow")
    table.add_column("Tools", justify="center")
    table.add_column("Stream", justify="center")
    table.add_column("Thinking", justify="center")
    table.add_column("Notes")

    for key, model in MODELS.items():
        table.add_row(
            key,
            model["name"],
            model["provider"],
            "✓" if model["supports_tools"] else "✗",
            "✓" if model["supports_streaming"] else "✗",
            "✓" if model["supports_thinking"] else "✗",
            model["notes"]
        )

    console.print(table)


def chat_with_model(model_name: str, use_tools: bool = False, use_streaming: bool = True):
    """Start an interactive chat session with the specified model."""
    client = LiteLLMClient()
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
                "messages": messages,
            }

            if use_tools and model_info["supports_tools"]:
                kwargs["tools"] = EXAMPLE_TOOLS

            # Make API call
            console.print("\n[bold green]Assistant[/bold green]")

            if use_streaming and model_info["supports_streaming"]:
                # Streaming response
                full_response = ""
                tool_calls = []

                try:
                    for chunk in client.chat.completions.create(**kwargs, stream=True):
                        if hasattr(chunk.choices[0], 'delta'):
                            delta = chunk.choices[0].delta

                            # Handle content
                            if hasattr(delta, 'content') and delta.content:
                                console.print(delta.content, end="")
                                full_response += delta.content

                            # Handle tool calls
                            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                                tool_calls.extend(delta.tool_calls)

                    console.print()  # New line after streaming

                    # Process tool calls if any
                    if tool_calls:
                        messages.append({
                            "role": "assistant",
                            "content": full_response or None,
                            "tool_calls": tool_calls
                        })

                        console.print("\n[yellow]🔧 Executing tools...[/yellow]")

                        for tool_call in tool_calls:
                            import json
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)

                            console.print(f"[dim]→ {tool_name}({tool_args})[/dim]")

                            result = execute_tool(tool_name, tool_args)

                            # Add tool response
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result
                            })

                        # Get final response with tool results
                        console.print("\n[bold green]Assistant (with tool results)[/bold green]")
                        final_response = ""

                        for chunk in client.chat.completions.create(
                            model=model_name,
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
                        messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    console.print(f"\n[red]Error: {str(e)}[/red]")
                    console.print(f"[dim]This might be due to missing API keys or model limitations.[/dim]")
                    messages.pop()  # Remove the user message if there was an error

            else:
                # Non-streaming response
                try:
                    response = client.chat.completions.create(**kwargs)
                    assistant_message = response.choices[0].message

                    if hasattr(assistant_message, 'content') and assistant_message.content:
                        console.print(assistant_message.content)
                        messages.append({"role": "assistant", "content": assistant_message.content})

                    # Handle tool calls
                    if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                        console.print("\n[yellow]🔧 Executing tools...[/yellow]")

                        messages.append({
                            "role": "assistant",
                            "tool_calls": assistant_message.tool_calls
                        })

                        for tool_call in assistant_message.tool_calls:
                            import json
                            tool_name = tool_call.function.name
                            tool_args = json.loads(tool_call.function.arguments)

                            console.print(f"[dim]→ {tool_name}({tool_args})[/dim]")

                            result = execute_tool(tool_name, tool_args)

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result
                            })

                        # Get final response
                        final = client.chat.completions.create(model=model_name, messages=messages)
                        final_content = final.choices[0].message.content
                        console.print(f"\n[bold green]Assistant (with tool results)[/bold green]\n{final_content}")
                        messages.append({"role": "assistant", "content": final_content})

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
        "Google": os.getenv("GOOGLE_API_KEY"),
    }

    console.print("\n[bold]API Key Status:[/bold]")
    for provider, key in api_keys.items():
        status = "✓" if key else "✗"
        color = "green" if key else "red"
        console.print(f"  [{color}]{status} {provider}[/{color}]")

    console.print()

    current_model = None

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

        # Ask about tools
        use_tools = Prompt.ask(
            "\n[bold]Enable tool calling?[/bold]",
            choices=["y", "n"],
            default="y"
        ) == "y"

        # Start chat
        result = chat_with_model(current_model, use_tools=use_tools)

        if result != "switch":
            break


if __name__ == "__main__":
    main()
