// State management
let currentModel = null;
let sessionMetrics = {
    promptTokens: 0,
    completionTokens: 0,
    totalTokens: 0
};

// DOM elements
const modelSelect = document.getElementById('model-select');
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

// Metric displays
const sessionPromptTokens = document.getElementById('session-prompt-tokens');
const sessionCompletionTokens = document.getElementById('session-completion-tokens');
const sessionTotalTokens = document.getElementById('session-total-tokens');

// Load available models on page load
async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();

        modelSelect.innerHTML = '<option value="">-- Select a model --</option>';

        data.models.forEach(model => {
            const option = document.createElement('option');
            option.value = JSON.stringify({ provider: model.provider, model: model.model, tools_support: model.tools_support });
            option.textContent = model.display;
            modelSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load models:', error);
        modelSelect.innerHTML = '<option value="">Error loading models</option>';
    }
}

// Load available tools on page load
async function loadTools() {
    const toolsList = document.getElementById('tools-list');
    try {
        const response = await fetch('/api/tools');
        const data = await response.json();

        if (data.tools && data.tools.length > 0) {
            toolsList.innerHTML = '';
            data.tools.forEach(tool => {
                const toolDiv = document.createElement('div');
                toolDiv.className = 'tool-item';

                const toolName = document.createElement('strong');
                toolName.textContent = tool.name;

                const toolDesc = document.createElement('p');
                toolDesc.textContent = tool.description;

                const paramsDiv = document.createElement('div');
                paramsDiv.className = 'tool-params';
                const paramsList = Object.entries(tool.parameters)
                    .map(([key, value]) => `${key}: ${value.type}${value.default ? ` (default: ${value.default})` : ''}`)
                    .join(', ');
                paramsDiv.textContent = `Parameters: ${paramsList}`;

                toolDiv.appendChild(toolName);
                toolDiv.appendChild(toolDesc);
                toolDiv.appendChild(paramsDiv);

                toolsList.appendChild(toolDiv);
            });
        } else {
            toolsList.innerHTML = '<div class="system-message">No tools available</div>';
        }
    } catch (error) {
        console.error('Failed to load tools:', error);
        toolsList.innerHTML = '<div class="system-message">Error loading tools</div>';
    }
}

// Reset session (clear chat and metrics)
function resetSession() {
    chatMessages.innerHTML = '<div class="system-message">Session reset. Start chatting!</div>';
    sessionMetrics = {
        promptTokens: 0,
        completionTokens: 0,
        totalTokens: 0
    };
    updateSessionMetrics();
}

// Update session metrics display
function updateSessionMetrics() {
    sessionPromptTokens.textContent = sessionMetrics.promptTokens;
    sessionCompletionTokens.textContent = sessionMetrics.completionTokens;
    sessionTotalTokens.textContent = sessionMetrics.totalTokens;
}

// Add message to chat
function addMessage(content, type, tokens = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const contentDiv = document.createElement('div');
    contentDiv.textContent = content;
    messageDiv.appendChild(contentDiv);

    if (tokens) {
        const tokensDiv = document.createElement('div');
        tokensDiv.className = 'message-tokens';
        tokensDiv.textContent = `Tokens: ${tokens.prompt} prompt + ${tokens.completion} completion = ${tokens.total} total`;
        messageDiv.appendChild(tokensDiv);
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || !currentModel) return;

    // Disable input while processing
    messageInput.disabled = true;
    sendButton.disabled = true;

    // Add user message
    addMessage(message, 'user');
    messageInput.value = '';

    // Add loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant-message loading';
    loadingDiv.textContent = 'Thinking...';
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                provider: currentModel.provider,
                model: currentModel.model,
                message: message,
                tools_support: currentModel.tools_support
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Remove loading indicator
        chatMessages.removeChild(loadingDiv);

        // Add assistant response
        addMessage(data.response, 'assistant', {
            prompt: data.prompt_tokens,
            completion: data.completion_tokens,
            total: data.total_tokens
        });

        // Update session metrics
        sessionMetrics.promptTokens += data.prompt_tokens;
        sessionMetrics.completionTokens += data.completion_tokens;
        sessionMetrics.totalTokens += data.total_tokens;
        updateSessionMetrics();

    } catch (error) {
        console.error('Failed to send message:', error);
        chatMessages.removeChild(loadingDiv);
        addMessage('Error: Failed to get response from the model. Please try again.', 'system');
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
    }
}

// Event listeners
modelSelect.addEventListener('change', (e) => {
    if (e.target.value) {
        currentModel = JSON.parse(e.target.value);
        updateInputState();
        resetSession();
        messageInput.focus();
    } else {
        currentModel = null;
        updateInputState();
    }
});

sendButton.addEventListener('click', sendMessage);

messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Update input state based on selections
function updateInputState() {
    if (currentModel) {
        messageInput.disabled = false;
        sendButton.disabled = false;
    } else {
        messageInput.disabled = true;
        sendButton.disabled = true;
    }
}

// Initialize
loadModels();
loadTools();

