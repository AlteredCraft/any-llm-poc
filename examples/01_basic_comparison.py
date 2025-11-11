#!/usr/bin/env python3
"""
Basic comparison: Same prompt across different models.
Shows how easy it is to switch models with any-llm.
"""

import os
from dotenv import load_dotenv
from any_llm import completion
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

# Models to compare (using provider:model format)
MODELS = [
    ("openai", "gpt-4o-mini"),
    ("anthropic", "claude-3-5-haiku-20241022"),
    ("mistral", "mistral-small-latest"),
]

PROMPT = "In one sentence, explain what makes Python a popular programming language."


def test_model(provider: str, model: str, prompt: str):
    """Test a single model with the given prompt."""
    console.print(f"\n[bold cyan]Testing: {provider}/{model}[/bold cyan]")

    try:
        response = completion(
            model=model,
            provider=provider,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )

        content = response.choices[0].message.content
        console.print(Panel(content, title=f"Response from {model}", border_style="green"))

    except Exception as e:
        console.print(f"[red]Error with {provider}/{model}: {str(e)}[/red]")
        console.print(f"[dim]Make sure you have the required API key set ({provider.upper()}_API_KEY).[/dim]")


def main():
    console.print(Panel.fit(
        "[bold blue]Basic Model Comparison[/bold blue]\n"
        "Testing the same prompt across different providers using any-llm",
        border_style="blue"
    ))

    console.print(f"\n[bold]Prompt:[/bold] {PROMPT}\n")

    for provider, model in MODELS:
        test_model(provider, model, PROMPT)

    console.print("\n[bold green]✓ Comparison complete![/bold green]")
    console.print("[dim]Notice how easy it was to switch between providers - just change the provider and model parameters![/dim]")
    console.print("[dim]any-llm uses the completion() function with consistent parameters across all providers.[/dim]")


if __name__ == "__main__":
    main()
