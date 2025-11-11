#!/usr/bin/env python3
"""
Capability matrix: Test which features work with which models.
Demonstrates how any-llm handles feature differences between providers.
"""

import os
from dotenv import load_dotenv
from any_llm import LiteLLMClient
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

load_dotenv()
console = Console()

MODELS_TO_TEST = [
    "gpt-4o-mini",
    "gpt-4o",
    "claude-3-5-haiku-20241022",
    "claude-3-5-sonnet-20241022",
    "mistral-large-latest",
    "gemini-2.0-flash-exp",
]

SIMPLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "test_function",
            "description": "A simple test function",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "A test message"}
                },
                "required": ["message"]
            }
        }
    }
]


def test_basic_completion(client: LiteLLMClient, model: str) -> bool:
    """Test basic chat completion."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}],
            max_tokens=50
        )
        return True
    except Exception:
        return False


def test_streaming(client: LiteLLMClient, model: str) -> bool:
    """Test streaming capability."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Count to 3."}],
            stream=True,
            max_tokens=50
        )
        # Consume stream
        for _ in response:
            pass
        return True
    except Exception:
        return False


def test_tool_calling(client: LiteLLMClient, model: str) -> bool:
    """Test tool calling capability."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Use the test_function to send 'hello'"}],
            tools=SIMPLE_TOOLS,
            max_tokens=150
        )
        # Check if tools were used
        if hasattr(response.choices[0].message, 'tool_calls'):
            return True
        return False
    except Exception:
        return False


def test_json_mode(client: LiteLLMClient, model: str) -> bool:
    """Test JSON mode capability."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": "Output a JSON object with a 'status' field set to 'ok'."}
            ],
            response_format={"type": "json_object"},
            max_tokens=50
        )
        return True
    except Exception:
        return False


def main():
    console.print(Panel.fit(
        "[bold blue]Model Capability Matrix[/bold blue]\n"
        "Testing features across different providers",
        border_style="blue"
    ))

    console.print("\n[dim]This may take a minute...[/dim]\n")

    client = LiteLLMClient()
    results = {}

    for model in MODELS_TO_TEST:
        console.print(f"[cyan]Testing {model}...[/cyan]")

        results[model] = {
            "basic": test_basic_completion(client, model),
            "streaming": test_streaming(client, model),
            "tools": test_tool_calling(client, model),
            "json_mode": test_json_mode(client, model),
        }

    # Display results table
    console.print()
    table = Table(title="Feature Support Matrix", show_header=True, header_style="bold magenta")

    table.add_column("Model", style="cyan", width=30)
    table.add_column("Basic", justify="center", width=8)
    table.add_column("Streaming", justify="center", width=10)
    table.add_column("Tools", justify="center", width=8)
    table.add_column("JSON Mode", justify="center", width=10)

    for model, features in results.items():
        table.add_row(
            model,
            "✓" if features["basic"] else "✗",
            "✓" if features["streaming"] else "✗",
            "✓" if features["tools"] else "✗",
            "✓" if features["json_mode"] else "✗",
        )

    console.print(table)

    console.print("\n[bold green]✓ Capability matrix complete![/bold green]")
    console.print("[dim]any-llm gracefully handles feature differences - unsupported features fail predictably.[/dim]")


if __name__ == "__main__":
    main()
