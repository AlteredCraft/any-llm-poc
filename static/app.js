// State management
let currentModel = null;
let currentUser = null;
let sessionMetrics = {
    promptTokens: 0,
    completionTokens: 0,
    totalTokens: 0
};

// DOM elements
const userSelect = document.getElementById('user-select');
const modelSelect = document.getElementById('model-select');
const chatMessages = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendButton = document.getElementById('send-button');

// Metric displays
const sessionPromptTokens = document.getElementById('session-prompt-tokens');
const sessionCompletionTokens = document.getElementById('session-completion-tokens');
const sessionTotalTokens = document.getElementById('session-total-tokens');
const totalPromptTokens = document.getElementById('total-prompt-tokens');
const totalCompletionTokens = document.getElementById('total-completion-tokens');
const totalTokens = document.getElementById('total-tokens');
const requestCount = document.getElementById('request-count');

// Load available users on page load
async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        const users = await response.json();

        userSelect.innerHTML = '<option value="">-- Select a user --</option>';

        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.user_id;
            option.textContent = user.alias ? `${user.alias} (${user.user_id})` : user.user_id;
            userSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load users:', error);
        userSelect.innerHTML = '<option value="">Error loading users</option>';
    }
}

// Load available models on page load
async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();

        modelSelect.innerHTML = '<option value="">-- Select a model --</option>';

        data.models.forEach(model => {
            const option = document.createElement('option');
            option.value = JSON.stringify({ provider: model.provider, model: model.model });
            option.textContent = model.display;
            modelSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load models:', error);
        modelSelect.innerHTML = '<option value="">Error loading models</option>';
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
    if (currentUser) {
        fetchTotalUsage();
    }
}

// Update session metrics display
function updateSessionMetrics() {
    sessionPromptTokens.textContent = sessionMetrics.promptTokens;
    sessionCompletionTokens.textContent = sessionMetrics.completionTokens;
    sessionTotalTokens.textContent = sessionMetrics.totalTokens;
}

// Fetch total usage from Gateway
async function fetchTotalUsage() {
    if (!currentUser) {
        totalPromptTokens.textContent = '-';
        totalCompletionTokens.textContent = '-';
        totalTokens.textContent = '-';
        requestCount.textContent = '-';
        return;
    }

    try {
        const response = await fetch(`/api/usage?user_id=${encodeURIComponent(currentUser)}`);
        const data = await response.json();

        totalPromptTokens.textContent = data.total_prompt_tokens;
        totalCompletionTokens.textContent = data.total_completion_tokens;
        totalTokens.textContent = data.total_tokens;
        requestCount.textContent = data.request_count;
    } catch (error) {
        console.error('Failed to fetch usage:', error);
        totalPromptTokens.textContent = 'Error';
        totalCompletionTokens.textContent = 'Error';
        totalTokens.textContent = 'Error';
        requestCount.textContent = 'Error';
    }
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
    if (!message || !currentModel || !currentUser) return;

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
                user_id: currentUser
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

        // Fetch updated total usage
        fetchTotalUsage();

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
userSelect.addEventListener('change', (e) => {
    if (e.target.value) {
        currentUser = e.target.value;
        updateInputState();
        resetSession();
    } else {
        currentUser = null;
        updateInputState();
    }
});

modelSelect.addEventListener('change', (e) => {
    if (e.target.value) {
        currentModel = JSON.parse(e.target.value);
        updateInputState();
        resetSession();
        if (currentUser && currentModel) {
            messageInput.focus();
        }
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
    if (currentUser && currentModel) {
        messageInput.disabled = false;
        sendButton.disabled = false;
    } else {
        messageInput.disabled = true;
        sendButton.disabled = true;
    }
}

// Initialize
loadUsers();
loadModels();
fetchTotalUsage();
