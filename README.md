# any-llm POC (Proof of Concept)

A minimal CLI chat application demonstrating the [any-llm](https://github.com/mozilla-ai/any-llm) library's capabilities, particularly focusing on:

- **Easy model switching** between providers (OpenAI, Anthropic, Mistral)
- **Feature delta management** - how the library handles differences in capabilities between models
- **Tool use / function calling** across different providers
- **Streaming responses** with consistent interface
- **Capability testing** to understand what each model supports

## What is any-llm?

`any-llm` is a Python SDK by Mozilla.ai that provides a single, standardized interface for communicating with multiple LLM providers including OpenAI, Anthropic, Mistral, and Ollama.

Key features:
- ✅ Uses official provider SDKs (not proxies)
- ✅ Consistent API across providers
- ✅ Supports streaming, tool calling, and more
- ✅ Pass Python functions directly as tools
- ✅ Full type hints for IDE support

## Project Structure

```
any-llm-poc/
├── chat.py                           # Main interactive CLI chat application
├── pyproject.toml                    # Project metadata and dependencies (uv)
├── requirements.txt                   # Python dependencies (pip fallback)
├── .python-version                   # Python version for uv
├── .env.example                      # Example environment variables
├── examples/
│   ├── 01_basic_comparison.py        # Compare same prompt across models
│   ├── 02_streaming_comparison.py    # Test streaming across providers
│   ├── 03_tool_calling.py            # Demonstrate tool/function calling
│   └── 04_capability_matrix.py       # Feature support matrix
└── README.md                         # This file
```

## Setup

### Prerequisites

This project requires Python 3.11 or higher.

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd any-llm-poc
```

### 2. Install Dependencies

#### Option A: Using uv (Recommended - Fast!)

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package installer and resolver.

Install uv if you haven't already:
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

Create virtual environment and install dependencies:
```bash
# Create venv and install dependencies in one command
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

Or use uv's shorthand:
```bash
# Run without activating venv
uv run python chat.py

# Or sync dependencies and create venv automatically
uv sync
```

#### Option B: Using pip (Traditional)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Dependencies installed:**
- `any-llm-sdk[all]` - The any-llm library with all provider support
- `python-dotenv` - For environment variable management
- `rich` - For beautiful terminal output

### 3. Configure API Keys

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MISTRAL_API_KEY=...
```

**Note:** You don't need all API keys - only for the providers you want to test.

### Why uv?

[uv](https://github.com/astral-sh/uv) is **10-100x faster** than pip for package installation and resolution. Key benefits:

- ⚡ **Blazing fast** - Written in Rust, installs packages in milliseconds
- 🔒 **Reliable** - Better dependency resolution than pip
- 🎯 **Modern** - Built for Python 3.11+ with full PEP 621 support
- 🛠️ **Convenient** - `uv run` lets you run scripts without activating venv
- 🔄 **Compatible** - Works with existing pip, virtualenv, and pyproject.toml

For this project, uv makes setup and running examples much faster!

## Usage

### Main Chat Application

Run the interactive chat app:

```bash
# With uv (if not in activated venv)
uv run python chat.py

# Or with activated venv (uv or pip)
python chat.py
```

Features:
- **Select models** from multiple providers
- **Switch models** mid-conversation with `/switch`
- **Toggle tool calling** on/off with `/tools`
- **Clear history** with `/clear`
- **See streaming responses** in real-time
- **Automatic tool execution** when enabled

Available commands in chat:
- `/switch` - Change to a different model
- `/tools` - Toggle tool calling on/off
- `/clear` - Clear conversation history
- `/quit` - Exit the application

### Example Scripts

#### 1. Basic Comparison

Test the same prompt across different models:

```bash
# With uv
uv run python examples/01_basic_comparison.py

# Or with activated venv
python examples/01_basic_comparison.py
```

**What it demonstrates:** How easy it is to switch between providers by just changing the provider and model parameters.

#### 2. Streaming Comparison

Compare streaming performance:

```bash
uv run python examples/02_streaming_comparison.py
```

**What it demonstrates:**
- Consistent streaming interface across providers
- Time-to-first-token metrics
- Total response time comparison

#### 3. Tool Calling

Test function calling across providers:

```bash
uv run python examples/03_tool_calling.py
```

**What it demonstrates:**
- Tool/function calling with OpenAI, Anthropic, and Mistral
- Passing Python functions directly as tools
- Multi-turn conversations with tool results

#### 4. Capability Matrix

Test which features work with which models:

```bash
uv run python examples/04_capability_matrix.py
```

**What it demonstrates:**
- Feature support across models
- How any-llm handles unsupported features
- Graceful degradation

## Key Insights

### 1. Model Switching is Trivial

Switching between providers is as simple as changing the provider and model parameters:

```python
from any_llm import completion

# OpenAI
response = completion(
    model="gpt-4o-mini",
    provider="openai",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Anthropic - just change the provider and model!
response = completion(
    model="claude-3-5-haiku-20241022",
    provider="anthropic",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### 2. Feature Delta Management

any-llm handles feature differences gracefully:

| Feature | OpenAI | Anthropic | Mistral |
|---------|--------|-----------|---------|
| Basic Chat | ✓ | ✓ | ✓ |
| Streaming | ✓ | ✓ | ✓ |
| Tool Calling | ✓ | ✓ | ✓ |
| JSON Mode | ✓ | Limited | ✓ |

**How it works:**
- Supported features work consistently across providers
- Unsupported features throw clear exceptions
- The library normalizes response formats

### 3. Tool Calling with Python Functions

The killer feature: pass Python functions directly as tools!

```python
def get_weather(location: str, unit: str = "fahrenheit") -> str:
    """Get the current weather for a location.

    Args:
        location: The city and state, e.g., San Francisco, CA
        unit: The temperature unit (celsius or fahrenheit)

    Returns:
        Weather information as a string
    """
    return f"The weather in {location} is sunny and 72°{unit[0].upper()}."

# Pass the function directly - any-llm handles the conversion!
response = completion(
    model="gpt-4o-mini",
    provider="openai",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=[get_weather]  # Just pass Python functions!
)
```

any-llm automatically converts your Python function into the proper tool format for each provider.

### 4. Streaming Works Consistently

Streaming has the same interface regardless of provider:

```python
for chunk in completion(
    model="gpt-4o-mini",
    provider="openai",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
):
    if hasattr(chunk.choices[0], 'delta'):
        delta = chunk.choices[0].delta
        if hasattr(delta, 'content') and delta.content:
            print(delta.content, end="")
```

## any-llm API Patterns

The library offers two main usage patterns:

### 1. Direct API Functions (Quick/Experimental)

```python
from any_llm import completion

response = completion(
    model="mistral-small-latest",
    provider="mistral",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

Best for: Scripts, notebooks, and quick experimentation.

### 2. AnyLLM Class (Production)

```python
from any_llm import AnyLLM

llm = AnyLLM.create("mistral", api_key="your-key")

response = llm.completion(
    model="mistral-small-latest",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

Best for: Production apps requiring connection pooling and multiple requests.

**This POC uses the direct API functions for simplicity.**

## Testing Different Capabilities

### Test Basic Chat

```bash
python chat.py
# Select a model and start chatting
```

### Test Tool Calling

```bash
python chat.py
# Enable tools when prompted
# Ask: "What's the weather in Paris?" or "Calculate 25 * 4"
```

### Test Model Switching

```bash
python chat.py
# Start chatting with one model
# Type: /switch
# Select a different model and continue
```

### Test Streaming

All models stream by default in the chat app. Watch the responses appear token by token!

## What Makes any-llm Special?

1. **No vendor lock-in** - Switch providers without code changes
2. **Official SDKs** - Uses official provider SDKs, not proxies
3. **Consistent interface** - Same API across all providers
4. **Python-first** - Pass Python functions directly as tools
5. **Graceful handling** - Clear errors for unsupported features
6. **Type hints** - Full IDE support with type annotations

## Observations & Findings

After testing this POC, key observations:

1. **Model switching is seamless** - Change providers with just 2 parameters
2. **Python tool support is amazing** - No need to write JSON schemas manually
3. **Error handling is clear** - Missing API keys and unsupported features give helpful errors
4. **Performance varies** - Different models have different latencies (test with streaming example)
5. **Tool calling works consistently** - Same code works across OpenAI, Anthropic, and Mistral
6. **Streaming is normalized** - All providers use the same streaming response format

## Limitations & Considerations

1. **API keys required** - You need valid API keys for each provider
2. **Rate limits** - Each provider has different rate limits
3. **Cost differences** - Pricing varies significantly between providers
4. **Feature gaps** - Some advanced features may not be available on all models
5. **Response formats** - While normalized, subtle differences may exist
6. **Python 3.11+ required** - The library requires Python 3.11 or higher

## Real-World Example: Tool Calling Workflow

Here's a complete example of the tool calling workflow:

```python
from any_llm import completion
import json

# 1. Define your tools as Python functions
def get_weather(location: str) -> str:
    """Get weather for a location."""
    # In production, call a real weather API
    return json.dumps({"temp": 72, "condition": "sunny"})

# 2. Make the initial request
response = completion(
    model="gpt-4o-mini",
    provider="openai",
    messages=[{"role": "user", "content": "What's the weather in NYC?"}],
    tools=[get_weather]
)

# 3. Execute tool calls if present
messages = [{"role": "user", "content": "What's the weather in NYC?"}]

if response.choices[0].message.tool_calls:
    messages.append({
        "role": "assistant",
        "tool_calls": response.choices[0].message.tool_calls
    })

    for tool_call in response.choices[0].message.tool_calls:
        result = get_weather(**json.loads(tool_call.function.arguments))
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })

    # 4. Get final response with tool results
    final = completion(
        model="gpt-4o-mini",
        provider="openai",
        messages=messages
    )
    print(final.choices[0].message.content)
```

## Quick Reference: uv Commands

Common uv commands for this project:

```bash
# Install dependencies
uv pip install -e .

# Run a script without activating venv
uv run python chat.py
uv run python examples/01_basic_comparison.py

# Create/recreate virtual environment
uv venv
uv venv --python 3.11

# Sync dependencies (reads pyproject.toml)
uv sync

# Add a new dependency
uv pip install <package-name>

# Update dependencies
uv pip install --upgrade <package-name>

# List installed packages
uv pip list

# Show dependency tree
uv pip tree
```

For more details, see [uv documentation](https://github.com/astral-sh/uv).

## Next Steps

To extend this POC:

1. **Add async support** - Use `acompletion()` for async workflows
2. **Add more providers** - Test with Ollama (local models) or other providers
3. **Implement error handling** - Add retry logic and better error messages
4. **Add conversation persistence** - Save and load chat histories
5. **Create benchmarks** - Compare quality, speed, and cost across models
6. **Test the AnyLLM class** - Compare connection pooling vs direct API

## Resources

### any-llm
- [any-llm GitHub](https://github.com/mozilla-ai/any-llm)
- [any-llm Documentation](https://mozilla-ai.github.io/any-llm/)
- [Mozilla.ai Blog: Introducing any-llm](https://blog.mozilla.ai/introducing-any-llm-a-unified-api-to-access-any-llm-provider/)
- [Mozilla.ai Blog: any-llm 1.0](https://blog.mozilla.ai/run-any-llm-with-a-single-api-introducing-any-llm-v1-0/)

### uv (Package Manager)
- [uv GitHub](https://github.com/astral-sh/uv)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Astral Blog: Introducing uv](https://astral.sh/blog/uv)

## License

MIT License - See LICENSE file for details.

## Contributing

This is a proof of concept. Feel free to fork and extend!

## Questions?

Check the examples and experiment with different models and features. The best way to understand any-llm is to play with it!

---

**Key Takeaway:** any-llm makes it trivial to switch between LLM providers. You can test OpenAI, Anthropic, and Mistral with the same code, just by changing two parameters. This POC demonstrates that promise in action.
