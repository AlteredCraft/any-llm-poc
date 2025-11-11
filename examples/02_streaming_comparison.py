#!/usr/bin/env python3
"""
Streaming comparison: Test streaming capabilities across models.
Shows how any-llm normalizes streaming responses.
"""

import os
import time
from dotenv import load_dotenv
from any_llm import LiteLLMClient
from rich.console import Console
from rich.panel import Panel
from rich.live import Live

load_dotenv()
console = Console()

MODELS = [
    "gpt-4o-mini",
    "claude-3-5-haiku-20241022",
]

PROMPT = "Write a short haiku about coding."


def test_streaming(client: LiteLLMClient, model: str, prompt: str):
    """Test streaming with a single model."""
    console.print(f"\n[bold cyan]Streaming from: {model}[/bold cyan]")

    try:
        start_time = time.time()
        full_response = ""
        first_token_time = None

        console.print("[dim]Response: [/dim]", end="")

        for chunk in client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        ):
            if hasattr(chunk.choices[0], 'delta'):
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    if first_token_time is None:
                        first_token_time = time.time()
                    console.print(delta.content, end="")
                    full_response += delta.content

        end_time = time.time()

        # Print timing info
        console.print()  # New line
        ttft = first_token_time - start_time if first_token_time else 0
        total_time = end_time - start_time

        console.print(f"\n[dim]Time to first token: {ttft:.2f}s[/dim]")
        console.print(f"[dim]Total time: {total_time:.2f}s[/dim]")
        console.print(f"[dim]Characters: {len(full_response)}[/dim]")

    except Exception as e:
        console.print(f"\n[red]Error with {model}: {str(e)}[/red]")


def main():
    console.print(Panel.fit(
        "[bold blue]Streaming Comparison[/bold blue]\n"
        "Compare streaming performance across providers",
        border_style="blue"
    ))

    console.print(f"\n[bold]Prompt:[/bold] {PROMPT}\n")

    client = LiteLLMClient()

    for model in MODELS:
        test_streaming(client, model, PROMPT)

    console.print("\n[bold green]✓ Streaming test complete![/bold green]")
    console.print("[dim]any-llm provides a consistent streaming interface across all providers.[/dim]")


if __name__ == "__main__":
    main()
