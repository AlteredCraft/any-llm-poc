# any-llm POC (Proof of Concept)

A minimal CLI chat application demonstrating the [any-llm](https://github.com/mozilla-ai/any-llm) library's capabilities, particularly focusing on:

- **Easy model switching** between providers (OpenAI, Anthropic, Mistral, Google)
- **Feature delta management** - how the library handles differences in capabilities between models
- **Tool use / function calling** across different providers
- **Streaming responses** with consistent interface
- **Capability testing** to understand what each model supports

## What is any-llm?

`any-llm` is a Python library by Mozilla.ai that provides a unified interface to communicate with different LLM providers. It allows you to switch between OpenAI, Anthropic, Mistral, Ollama, Google, and more without changing your code.

Key features:
- ✅ Uses official SDKs (no proxies)
- ✅ Consistent API across providers
- ✅ Supports streaming, tool calling, and more
- ✅ OpenAI-compatible response format

## Project Structure

```
any-llm-poc/
├── chat.py                           # Main interactive CLI chat application
├── requirements.txt                   # Python dependencies
├── .env.example                      # Example environment variables
├── examples/
│   ├── 01_basic_comparison.py        # Compare same prompt across models
│   ├── 02_streaming_comparison.py    # Test streaming across providers
│   ├── 03_tool_calling.py            # Demonstrate tool/function calling
│   └── 04_capability_matrix.py       # Feature support matrix
└── README.md                         # This file
```

## Setup

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd any-llm-poc
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
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
GOOGLE_API_KEY=...
```

**Note:** You don't need all API keys - only for the providers you want to test.

## Usage

### Main Chat Application

Run the interactive chat app:

```bash
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
python examples/01_basic_comparison.py
```

**What it demonstrates:** How easy it is to switch between providers by just changing the model name.

#### 2. Streaming Comparison

Compare streaming performance:

```bash
python examples/02_streaming_comparison.py
```

**What it demonstrates:**
- Consistent streaming interface across providers
- Time-to-first-token metrics
- Total response time comparison

#### 3. Tool Calling

Test function calling across providers:

```bash
python examples/03_tool_calling.py
```

**What it demonstrates:**
- Tool/function calling with OpenAI, Anthropic, etc.
- Consistent tool calling interface
- Multi-turn conversations with tool results

#### 4. Capability Matrix

Test which features work with which models:

```bash
python examples/04_capability_matrix.py
```

**What it demonstrates:**
- Feature support across models
- How any-llm handles unsupported features
- Graceful degradation

## Key Insights

### 1. Model Switching is Trivial

Switching between providers is as simple as changing the model name:

```python
from any_llm import LiteLLMClient

client = LiteLLMClient()

# OpenAI
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Anthropic - just change the model name!
response = client.chat.completions.create(
    model="claude-3-5-haiku-20241022",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### 2. Feature Delta Management

any-llm handles feature differences gracefully:

| Feature | OpenAI | Anthropic | Mistral | Google |
|---------|--------|-----------|---------|--------|
| Basic Chat | ✓ | ✓ | ✓ | ✓ |
| Streaming | ✓ | ✓ | ✓ | ✓ |
| Tool Calling | ✓ | ✓ | ✓ | ✓ |
| JSON Mode | ✓ | Varies | ✓ | ✓ |

**How it works:**
- Supported features work consistently across providers
- Unsupported features throw clear exceptions
- The library normalizes response formats

### 3. Tool Calling is Unified

Tool calling syntax is consistent across providers:

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    }
}]

# Works with any provider that supports tools
response = client.chat.completions.create(
    model="gpt-4o-mini",  # or "claude-3-5-haiku-20241022", etc.
    messages=messages,
    tools=tools
)
```

### 4. Streaming Works Consistently

Streaming has the same interface regardless of provider:

```python
for chunk in client.chat.completions.create(
    model=model_name,  # Any model
    messages=messages,
    stream=True
):
    if hasattr(chunk.choices[0], 'delta'):
        delta = chunk.choices[0].delta
        if hasattr(delta, 'content') and delta.content:
            print(delta.content, end="")
```

## Testing Different Capabilities

### Test Basic Chat

```python
python chat.py
# Select a model and start chatting
```

### Test Tool Calling

```python
python chat.py
# Enable tools when prompted
# Ask: "What's the weather in Paris?"
```

### Test Model Switching

```python
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
3. **Consistent interface** - OpenAI-compatible API across all providers
4. **Graceful handling** - Clear errors for unsupported features
5. **Simple implementation** - Minimal code needed to get started

## Observations & Findings

After testing this POC, key observations:

1. **Model switching is seamless** - Change providers in one line
2. **Feature parity is good** - Most modern models support tools and streaming
3. **Error handling is clear** - Missing API keys and unsupported features give helpful errors
4. **Performance varies** - Different models have different latencies (test with streaming example)
5. **Tool calling works great** - Consistent implementation across providers

## Limitations & Considerations

1. **API keys required** - You need valid API keys for each provider
2. **Rate limits** - Each provider has different rate limits
3. **Cost differences** - Pricing varies significantly between providers
4. **Feature gaps** - Some advanced features may not be available on all models
5. **Response formats** - While normalized, subtle differences may exist

## Next Steps

To extend this POC:

1. **Add more models** - Test with additional providers (AWS Bedrock, Azure, etc.)
2. **Implement error handling** - Add retry logic and better error messages
3. **Add conversation persistence** - Save and load chat histories
4. **Create benchmarks** - Compare quality, speed, and cost across models
5. **Test edge cases** - Large contexts, multi-modal inputs, etc.

## Resources

- [any-llm GitHub](https://github.com/mozilla-ai/any-llm)
- [any-llm Documentation](https://mozilla-ai.github.io/any-llm/)
- [Mozilla.ai Blog Post](https://blog.mozilla.ai/introducing-any-llm-a-unified-api-to-access-any-llm-provider/)

## License

MIT License - See LICENSE file for details.

## Contributing

This is a proof of concept. Feel free to fork and extend!

## Questions?

Check the examples and experiment with different models and features. The best way to understand any-llm is to play with it!
