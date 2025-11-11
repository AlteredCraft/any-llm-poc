#!/usr/bin/env python3
"""
Basic comparison: Same prompt across different models.
Shows how easy it is to switch models with any-llm.
"""

import os
from dotenv import load_dotenv
from any_llm import LiteLLMClient
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

# Models to compare
MODELS = [
    "gpt-4o-mini",
    "claude-3-5-haiku-20241022",
    "mistral-large-latest",
]

PROMPT = "In one sentence, explain what makes Python a popular programming language."


def test_model(client: LiteLLMClient, model: str, prompt: str):
    """Test a single model with the given prompt."""
    console.print(f"\n[bold cyan]Testing: {model}[/bold cyan]")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )

        content = response.choices[0].message.content
        console.print(Panel(content, title=f"Response from {model}", border_style="green"))

    except Exception as e:
        console.print(f"[red]Error with {model}: {str(e)}[/red]")
        console.print(f"[dim]Make sure you have the required API key set.[/dim]")


def main():
    console.print(Panel.fit(
        "[bold blue]Basic Model Comparison[/bold blue]\n"
        "Testing the same prompt across different providers",
        border_style="blue"
    ))

    console.print(f"\n[bold]Prompt:[/bold] {PROMPT}\n")

    client = LiteLLMClient()

    for model in MODELS:
        test_model(client, model, PROMPT)

    console.print("\n[bold green]✓ Comparison complete![/bold green]")
    console.print("[dim]Notice how easy it was to switch between providers - just change the model name![/dim]")


if __name__ == "__main__":
    main()
