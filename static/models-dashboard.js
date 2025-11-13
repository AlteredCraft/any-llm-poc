// Global state
let models = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadModels();
});

// Load models from API
async function loadModels() {
    try {
        const response = await fetch('/api/admin/models/config');
        const data = await response.json();
        models = data.models;
        renderModelsTable();
    } catch (error) {
        showAlert('Failed to load models: ' + error.message, 'error');
    }
}

// Render models table
function renderModelsTable() {
    const container = document.getElementById('modelsTable');

    if (models.length === 0) {
        container.innerHTML = '<div class="empty-state">No models configured. Click "Add New Model" to get started.</div>';
        return;
    }

    const table = `
        <table>
            <thead>
                <tr>
                    <th>Provider</th>
                    <th>Model ID</th>
                    <th>Display Name</th>
                    <th>Tools Support</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${models.map(model => `
                    <tr>
                        <td><span class="provider-badge provider-${model.provider}">${model.provider}</span></td>
                        <td><code>${model.model}</code></td>
                        <td>${model.display}</td>
                        <td><span class="badge badge-${model.tools_support ? 'yes' : 'no'}">${model.tools_support ? 'Yes' : 'No'}</span></td>
                        <td>
                            <button class="btn btn-danger" onclick="deleteModel('${model.provider}', '${model.model}')">Delete</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = table;
}

// Show alert message
function showAlert(message, type = 'success') {
    const alert = document.getElementById('alert');
    alert.className = `alert alert-${type} active`;
    alert.textContent = message;

    setTimeout(() => {
        alert.className = 'alert';
    }, 5000);
}

// Open add modal
function openAddModal() {
    document.getElementById('modalTitle').textContent = 'Add New Model';
    document.getElementById('modelForm').reset();
    document.getElementById('modelModal').classList.add('active');
}

// Close modal
function closeModal() {
    document.getElementById('modelModal').classList.remove('active');
    document.getElementById('modelForm').reset();
}

// Save model (add new)
async function saveModel(event) {
    event.preventDefault();

    const modelData = {
        provider: document.getElementById('provider').value,
        model: document.getElementById('model').value,
        display: document.getElementById('display').value,
        tools_support: document.getElementById('tools_support').checked
    };

    try {
        const response = await fetch('/api/admin/models/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(modelData)
        });

        const result = await response.json();

        if (response.ok) {
            showAlert(result.message, 'success');
            closeModal();
            await loadModels();
        } else {
            showAlert(result.detail || 'Failed to add model', 'error');
        }
    } catch (error) {
        showAlert('Failed to add model: ' + error.message, 'error');
    }
}

// Delete model
async function deleteModel(provider, model) {
    if (!confirm(`Are you sure you want to delete ${provider}:${model}?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/models/config/${encodeURIComponent(provider)}/${encodeURIComponent(model)}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (response.ok) {
            showAlert(result.message, 'success');
            await loadModels();
        } else {
            showAlert(result.detail || 'Failed to delete model', 'error');
        }
    } catch (error) {
        showAlert('Failed to delete model: ' + error.message, 'error');
    }
}

// Reload configuration from file
async function reloadConfig() {
    try {
        const response = await fetch('/api/admin/models/reload', {
            method: 'POST'
        });

        const result = await response.json();

        if (response.ok) {
            showAlert(result.message, 'success');
            await loadModels();
        } else {
            showAlert(result.detail || 'Failed to reload configuration', 'error');
        }
    } catch (error) {
        showAlert('Failed to reload configuration: ' + error.message, 'error');
    }
}

// Export configuration
function exportConfig() {
    const dataStr = JSON.stringify(models, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = 'models_config_export.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    showAlert('Configuration exported successfully', 'success');
}

// Close modal when clicking outside
document.getElementById('modelModal').addEventListener('click', (event) => {
    if (event.target.id === 'modelModal') {
        closeModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeModal();
    }
});
