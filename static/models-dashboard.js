// Global state
let models = [];
let discoveredModels = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Bootstrap modals
    if (typeof bootstrap !== 'undefined') {
        modelModal = new bootstrap.Modal(document.getElementById('modelModal'));
        discoveryModal = new bootstrap.Modal(document.getElementById('discoveryModal'));
    }
    loadModels();
    initializeDiscoverySelect();
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
        container.innerHTML = '<div class="empty-state"><i class="bi bi-inbox"></i><p>No models configured. Click "Add New Model" to get started.</p></div>';
        return;
    }

    const table = `
        <div class="table-responsive">
            <table class="table table-hover">
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
                                <button class="btn btn-danger btn-sm" onclick="deleteModel('${model.provider}', '${model.model}')">
                                    <i class="bi bi-trash me-1"></i>Delete
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = table;
}

// Show alert message
function showAlert(message, type = 'success') {
    const alert = document.getElementById('alert');
    const alertContent = document.getElementById('alert-content');
    alert.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alert.style.display = 'block';
    alertContent.textContent = message;

    setTimeout(() => {
        alert.style.display = 'none';
    }, 5000);
}

// Bootstrap modal instances
let modelModal;
let discoveryModal;

// Open add modal
function openAddModal() {
    document.getElementById('modalTitle').innerHTML = '<i class="bi bi-plus-circle me-2"></i>Add New Model';
    document.getElementById('modelForm').reset();
    if (modelModal) {
        modelModal.show();
    }
}

// Close modal
function closeModal() {
    if (modelModal) {
        modelModal.hide();
    }
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

// Bootstrap handles modal closing with backdrop click and Escape key automatically

// ========== Model Discovery Functions ==========

// Initialize discovery provider select
function initializeDiscoverySelect() {
    const select = document.getElementById('discovery-provider');
    const btn = document.getElementById('discover-btn');

    select.addEventListener('change', (e) => {
        btn.disabled = !e.target.value;
    });
}

// Discover models from selected provider
async function discoverModels() {
    const select = document.getElementById('discovery-provider');
    const provider = select.value;

    if (!provider) {
        showAlert('Please select a provider', 'error');
        return;
    }

    const btn = document.getElementById('discover-btn');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Discovering...';

    try {
        const response = await fetch(`/api/providers/${provider}/discover`);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        discoveredModels = data.models;

        if (discoveredModels.length === 0) {
            showAlert(`No models found for ${provider}`, 'error');
        } else {
            showAlert(`Discovered ${discoveredModels.length} models from ${provider}`, 'success');
            openDiscoveryModal(provider);
        }
    } catch (error) {
        showAlert(`Failed to discover models: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

// Open discovery modal with results
function openDiscoveryModal(provider) {
    const modal = document.getElementById('discoveryModal');
    const title = document.getElementById('discoveryModalTitle');
    const content = document.getElementById('discoveryContent');

    title.textContent = `Discovered Models from ${provider.charAt(0).toUpperCase() + provider.slice(1)}`;

    if (discoveredModels.length === 0) {
        content.innerHTML = '<div class="empty-state"><i class="bi bi-inbox"></i><p>No models discovered</p></div>';
    } else {
        content.innerHTML = `
            <p class="text-muted mb-3">
                Found <strong>${discoveredModels.length}</strong> models. Select the ones you want to add to your configuration:
            </p>
            <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th style="width: 60px;">Select</th>
                            <th>Model Name</th>
                            <th>Display Name</th>
                            <th>Tools Support</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${discoveredModels.map((model, index) => `
                            <tr>
                                <td>
                                    <input type="checkbox" class="form-check-input" id="model-${index}" data-index="${index}"
                                           ${isModelAlreadyAdded(model) ? 'disabled checked' : ''}>
                                </td>
                                <td><code>${model.model}</code></td>
                                <td>${model.display}</td>
                                <td><span class="badge badge-${model.tools_support ? 'yes' : 'no'}">${model.tools_support ? 'Yes' : 'No'}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="d-flex gap-2 mt-3">
                <button class="btn btn-primary" onclick="addSelectedModels()">
                    <i class="bi bi-plus-lg me-2"></i>Add Selected Models
                </button>
                <button class="btn btn-outline-secondary" onclick="selectAllDiscovered()">Select All</button>
                <button class="btn btn-outline-secondary" onclick="deselectAllDiscovered()">Deselect All</button>
            </div>
        `;
    }

    if (discoveryModal) {
        discoveryModal.show();
    }
}

// Close discovery modal
function closeDiscoveryModal() {
    if (discoveryModal) {
        discoveryModal.hide();
    }
    discoveredModels = [];
}

// Check if model is already added
function isModelAlreadyAdded(discoveredModel) {
    return models.some(m =>
        m.provider === discoveredModel.provider &&
        m.model === discoveredModel.model
    );
}

// Select all discovered models
function selectAllDiscovered() {
    discoveredModels.forEach((_, index) => {
        const checkbox = document.getElementById(`model-${index}`);
        if (checkbox && !checkbox.disabled) {
            checkbox.checked = true;
        }
    });
}

// Deselect all discovered models
function deselectAllDiscovered() {
    discoveredModels.forEach((_, index) => {
        const checkbox = document.getElementById(`model-${index}`);
        if (checkbox && !checkbox.disabled) {
            checkbox.checked = false;
        }
    });
}

// Add selected models to configuration
async function addSelectedModels() {
    const selectedIndices = [];
    discoveredModels.forEach((_, index) => {
        const checkbox = document.getElementById(`model-${index}`);
        if (checkbox && checkbox.checked && !checkbox.disabled) {
            selectedIndices.push(index);
        }
    });

    if (selectedIndices.length === 0) {
        showAlert('Please select at least one model to add', 'error');
        return;
    }

    const modelsToAdd = selectedIndices.map(index => discoveredModels[index]);

    let successCount = 0;
    let errorCount = 0;

    for (const model of modelsToAdd) {
        try {
            const response = await fetch('/api/admin/models/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(model)
            });

            if (response.ok) {
                successCount++;
            } else {
                errorCount++;
                const error = await response.json();
                console.error(`Failed to add ${model.model}: ${error.detail}`);
            }
        } catch (error) {
            errorCount++;
            console.error(`Failed to add ${model.model}:`, error);
        }
    }

    if (successCount > 0) {
        showAlert(`Successfully added ${successCount} model(s)${errorCount > 0 ? ` (${errorCount} failed)` : ''}`, 'success');
        await loadModels();
        closeDiscoveryModal();
    } else {
        showAlert(`Failed to add models`, 'error');
    }
}

// Bootstrap handles discovery modal closing automatically

// Toggle models list expansion
function toggleModelsList() {
    const container = document.getElementById('modelsTableContainer');
    const btn = document.getElementById('toggleListBtn');

    if (container.classList.contains('collapsed')) {
        container.classList.remove('collapsed');
        container.classList.add('expanded');
        btn.innerHTML = '<i class="bi bi-arrows-collapse me-1"></i>Collapse';
    } else {
        container.classList.remove('expanded');
        container.classList.add('collapsed');
        btn.innerHTML = '<i class="bi bi-arrows-expand me-1"></i>Expand';
        // Scroll the Available Models card into view when collapsing
        document.querySelector('.card').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}
