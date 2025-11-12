// DOM elements
const createUserBtn = document.getElementById('create-user-btn');
const newUserIdInput = document.getElementById('new-user-id');
const newUserAliasInput = document.getElementById('new-user-alias');
const userCreationMessage = document.getElementById('user-creation-message');
const usersTableBody = document.getElementById('users-table-body');

// Global stats elements
const globalUsers = document.getElementById('global-users');
const globalRequests = document.getElementById('global-requests');
const globalTokens = document.getElementById('global-tokens');
const globalCost = document.getElementById('global-cost');
const globalPromptTokens = document.getElementById('global-prompt-tokens');
const globalCompletionTokens = document.getElementById('global-completion-tokens');

// Fetch and display global usage
async function fetchGlobalUsage() {
    try {
        const response = await fetch('/api/usage/global');
        const data = await response.json();

        globalUsers.textContent = data.total_users.toLocaleString();
        globalRequests.textContent = data.total_requests.toLocaleString();
        globalTokens.textContent = data.total_tokens.toLocaleString();
        globalCost.textContent = `$${(data.total_cost || 0).toFixed(4)}`;
        globalPromptTokens.textContent = data.total_prompt_tokens.toLocaleString();
        globalCompletionTokens.textContent = data.total_completion_tokens.toLocaleString();
    } catch (error) {
        console.error('Failed to fetch global usage:', error);
        globalUsers.textContent = 'Error';
        globalRequests.textContent = 'Error';
        globalTokens.textContent = 'Error';
        globalCost.textContent = 'Error';
        globalPromptTokens.textContent = 'Error';
        globalCompletionTokens.textContent = 'Error';
    }
}

// Fetch and display per-user usage
async function fetchUsersUsage() {
    try {
        const response = await fetch('/api/usage/users');
        const users = await response.json();

        if (users.length === 0) {
            usersTableBody.innerHTML = '<tr><td colspan="7" class="empty">No users found</td></tr>';
            return;
        }

        usersTableBody.innerHTML = users.map(user => `
            <tr>
                <td>${escapeHtml(user.user_id)}</td>
                <td>${user.alias ? escapeHtml(user.alias) : '-'}</td>
                <td>${user.request_count.toLocaleString()}</td>
                <td>${user.prompt_tokens.toLocaleString()}</td>
                <td>${user.completion_tokens.toLocaleString()}</td>
                <td>${user.total_tokens.toLocaleString()}</td>
                <td>$${(user.cost || 0).toFixed(4)}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to fetch users usage:', error);
        usersTableBody.innerHTML = '<tr><td colspan="7" class="error">Failed to load users</td></tr>';
    }
}

// Create a new user
async function createUser() {
    const userId = newUserIdInput.value.trim();
    const alias = newUserAliasInput.value.trim() || null;

    if (!userId) {
        showMessage('Please enter a User ID', 'error');
        return;
    }

    // Disable button while processing
    createUserBtn.disabled = true;
    createUserBtn.textContent = 'Creating...';

    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                alias: alias
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        showMessage(`User "${userId}" created successfully!`, 'success');

        // Clear inputs
        newUserIdInput.value = '';
        newUserAliasInput.value = '';

        // Refresh the dashboard
        await refreshDashboard();

    } catch (error) {
        console.error('Failed to create user:', error);
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        createUserBtn.disabled = false;
        createUserBtn.textContent = 'Create User';
    }
}

// Show message
function showMessage(text, type) {
    userCreationMessage.textContent = text;
    userCreationMessage.className = `message ${type}`;

    // Clear message after 5 seconds
    setTimeout(() => {
        userCreationMessage.textContent = '';
        userCreationMessage.className = 'message';
    }, 5000);
}

// Refresh dashboard data
async function refreshDashboard() {
    await Promise.all([
        fetchGlobalUsage(),
        fetchUsersUsage()
    ]);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event listeners
createUserBtn.addEventListener('click', createUser);

newUserIdInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        createUser();
    }
});

newUserAliasInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        createUser();
    }
});

// Initialize dashboard
refreshDashboard();

// Refresh dashboard every 30 seconds
setInterval(refreshDashboard, 30000);
