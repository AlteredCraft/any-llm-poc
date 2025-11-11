#!/usr/bin/env python3
"""
Capability matrix: Test which features work with which models.
Demonstrates how any-llm handles feature differences between providers.
"""

import os
from dotenv import load_dotenv
from any_llm import completion
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

load_dotenv()
console = Console()

MODELS_TO_TEST = [
    ("openai", "gpt-4o-mini"),
    ("openai", "gpt-4o"),
    ("anthropic", "claude-3-5-haiku-20241022"),
    ("anthropic", "claude-3-5-sonnet-20241022"),
    ("mistral", "mistral-small-latest"),
    ("mistral", "mistral-large-latest"),
]


def test_function(message: str) -> str:
    """A simple test function.

    Args:
        message: A test message

    Returns:
        Echo of the message
    """
    return f"Received: {message}"


SIMPLE_TOOLS = [test_function]


def test_basic_completion(provider: str, model: str) -> bool:
    """Test basic chat completion."""
    try:
        response = completion(
            model=model,
            provider=provider,
            messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}],
            max_tokens=50
        )
        return bool(response.choices[0].message.content)
    except Exception:
        return False


def test_streaming(provider: str, model: str) -> bool:
    """Test streaming capability."""
    try:
        chunks_received = 0
        for chunk in completion(
            model=model,
            provider=provider,
            messages=[{"role": "user", "content": "Count to 3."}],
            stream=True,
            max_tokens=50
        ):
            chunks_received += 1
            if chunks_received >= 1:  # At least one chunk
                break
        return chunks_received > 0
    except Exception:
        return False


def test_tool_calling(provider: str, model: str) -> bool:
    """Test tool calling capability."""
    try:
        response = completion(
            model=model,
            provider=provider,
            messages=[{"role": "user", "content": "Use the test_function to send 'hello'"}],
            tools=SIMPLE_TOOLS,
            max_tokens=150
        )
        # Check if tools were used
        if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
            return True
        return False
    except Exception:
        return False


def test_json_mode(provider: str, model: str) -> bool:
    """Test JSON mode capability (if supported)."""
    try:
        response = completion(
            model=model,
            provider=provider,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": "Output a JSON object with a 'status' field set to 'ok'."}
            ],
            response_format={"type": "json_object"},
            max_tokens=50
        )
        return bool(response.choices[0].message.content)
    except Exception:
        return False


def main():
    console.print(Panel.fit(
        "[bold blue]Model Capability Matrix[/bold blue]\n"
        "Testing features across different providers using any-llm",
        border_style="blue"
    ))

    console.print("\n[dim]This may take a minute...[/dim]\n")

    results = {}

    for provider, model in MODELS_TO_TEST:
        console.print(f"[cyan]Testing {provider}/{model}...[/cyan]")

        results[f"{provider}/{model}"] = {
            "basic": test_basic_completion(provider, model),
            "streaming": test_streaming(provider, model),
            "tools": test_tool_calling(provider, model),
            "json_mode": test_json_mode(provider, model),
        }

    # Display results table
    console.print()
    table = Table(title="Feature Support Matrix", show_header=True, header_style="bold magenta")

    table.add_column("Provider/Model", style="cyan", width=35)
    table.add_column("Basic", justify="center", width=8)
    table.add_column("Streaming", justify="center", width=10)
    table.add_column("Tools", justify="center", width=8)
    table.add_column("JSON Mode", justify="center", width=10)

    for model_key, features in results.items():
        table.add_row(
            model_key,
            "✓" if features["basic"] else "✗",
            "✓" if features["streaming"] else "✗",
            "✓" if features["tools"] else "✗",
            "✓" if features["json_mode"] else "✗",
        )

    console.print(table)

    console.print("\n[bold green]✓ Capability matrix complete![/bold green]")
    console.print("[dim]any-llm provides consistent APIs across providers.[/dim]")
    console.print("[dim]Features that aren't supported will fail gracefully with clear errors.[/dim]")


if __name__ == "__main__":
    main()
