// frontend/js/integration.js

// ---------- AUTH CHECK – MANAGER/ADMIN ONLY ----------
(async function() {
    const user = await checkAuth(['manager', 'admin']);
    if (!user) return;
    window.currentUser = user;
    loadIntegrationData();
})();

// ---------- LOGOUT ----------
document.getElementById('logoutLink').addEventListener('click', (e) => {
    e.preventDefault();
    logout();
});

// ---------- GLOBAL ----------
let editingWebhookId = null;

// ---------- LOAD ALL INTEGRATION DATA ----------
async function loadIntegrationData() {
    await loadApiKeys();
    await loadWebhooks();
    await loadStatus();
    await loadDeliveries();
}

// ---------- API KEYS ----------
async function loadApiKeys() {
    const token = localStorage.getItem('access_token');
    const listDiv = document.getElementById('apiKeysList');
    try {
        const response = await fetch('/integration/api-keys', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to load API keys');
        const keys = await response.json();
        if (keys.length === 0) {
            listDiv.innerHTML = '<p class="text-muted">No API keys created yet.</p>';
            return;
        }
        let html = '';
        keys.forEach(k => {
            const expires = k.expires_at ? new Date(k.expires_at).toLocaleDateString() : 'Never';
            const statusClass = k.is_active ? 'badge-success' : 'badge-secondary';
            html += `
                <div class="webhook-row">
                    <div>
                        <strong>${k.name}</strong><br>
                        <span class="api-key-box">${k.api_key}</span><br>
                        <small>Expires: ${expires} | Last used: ${k.last_used_at ? new Date(k.last_used_at).toLocaleString() : 'Never'}</small>
                    </div>
                    <div>
                        <span class="badge ${statusClass}">${k.is_active ? 'Active' : 'Revoked'}</span>
                        <button onclick="regenerateApiKey(${k.id})" class="btn" style="padding:5px 10px;">⟲ Regenerate</button>
                        ${k.is_active ? `<button onclick="revokeApiKey(${k.id})" class="btn btn-danger" style="padding:5px 10px;">Revoke</button>` : ''}
                    </div>
                </div>
            `;
        });
        listDiv.innerHTML = html;
    } catch (error) {
        listDiv.innerHTML = '<p class="alert alert-error">Error loading API keys.</p>';
    }
}

// ---------- API Key actions ----------
document.getElementById('addApiKeyBtn').addEventListener('click', () => {
    document.getElementById('apiKeyFormContainer').style.display = 'block';
});

document.getElementById('cancelApiKeyBtn').addEventListener('click', () => {
    document.getElementById('apiKeyFormContainer').style.display = 'none';
    document.getElementById('apiKeyName').value = '';
    document.getElementById('apiKeyExpiry').value = '';
});

document.getElementById('saveApiKeyBtn').addEventListener('click', async () => {
    const name = document.getElementById('apiKeyName').value.trim();
    const expiry = document.getElementById('apiKeyExpiry').value;
    if (!name) {
        showAlert('Please enter a name', 'error');
        return;
    }
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch('/integration/api-keys', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                name: name,
                expires_in_days: expiry ? parseInt(expiry) : null
            })
        });
        if (response.ok) {
            showAlert('API key created successfully', 'success');
            document.getElementById('apiKeyFormContainer').style.display = 'none';
            document.getElementById('apiKeyName').value = '';
            document.getElementById('apiKeyExpiry').value = '';
            loadApiKeys();
            loadStatus();
        } else {
            const err = await response.json();
            showAlert(err.detail || 'Creation failed', 'error');
        }
    } catch (error) {
        showAlert('Network error', 'error');
    }
});

window.regenerateApiKey = async function(id) {
    if (!confirm('Regenerate API key? The old key will stop working immediately.')) return;
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`/integration/api-keys/${id}/regenerate`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
            showAlert('API key regenerated', 'success');
            loadApiKeys();
        } else {
            const err = await response.json();
            showAlert(err.detail || 'Failed', 'error');
        }
    } catch (error) {
        showAlert('Network error', 'error');
    }
};

window.revokeApiKey = async function(id) {
    if (!confirm('Revoke this API key? It will no longer work.')) return;
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`/integration/api-keys/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
            showAlert('API key revoked', 'success');
            loadApiKeys();
            loadStatus();
        } else {
            const err = await response.json();
            showAlert(err.detail || 'Failed', 'error');
        }
    } catch (error) {
        showAlert('Network error', 'error');
    }
};

// ---------- WEBHOOKS ----------
async function loadWebhooks() {
    const token = localStorage.getItem('access_token');
    const listDiv = document.getElementById('webhooksList');
    try {
        const response = await fetch('/integration/webhooks', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to load webhooks');
        const webhooks = await response.json();
        if (webhooks.length === 0) {
            listDiv.innerHTML = '<p class="text-muted">No webhooks configured.</p>';
            return;
        }
        let html = '';
        webhooks.forEach(w => {
            const events = w.events.map(e => `<span class="event-tag">${e}</span>`).join('');
            const statusClass = w.is_active ? 'badge-success' : 'badge-secondary';
            html += `
                <div class="webhook-row">
                    <div>
                        <strong>${w.name}</strong><br>
                        <span style="font-size:13px;">${w.url}</span><br>
                        <div style="margin-top:5px;">${events}</div>
                        <small>Created: ${new Date(w.created_at).toLocaleDateString()}</small>
                    </div>
                    <div>
                        <span class="badge ${statusClass}">${w.is_active ? 'Active' : 'Inactive'}</span>
                        <button onclick="editWebhook(${w.id})" class="btn" style="padding:5px 10px;">Edit</button>
                        <button onclick="deleteWebhook(${w.id})" class="btn btn-danger" style="padding:5px 10px;">Delete</button>
                    </div>
                </div>
            `;
        });
        listDiv.innerHTML = html;
    } catch (error) {
        listDiv.innerHTML = '<p class="alert alert-error">Error loading webhooks.</p>';
    }
}

// ---------- Webhook form ----------
function showWebhookForm(webhook = null) {
    const form = document.getElementById('webhookFormContainer');
    document.getElementById('webhookFormTitle').textContent = webhook ? 'Edit Webhook' : 'Create Webhook';
    if (webhook) {
        document.getElementById('webhookId').value = webhook.id;
        document.getElementById('webhookName').value = webhook.name;
        document.getElementById('webhookUrl').value = webhook.url;
        document.getElementById('webhookSecret').value = webhook.secret || '';
        // Check checkboxes
        document.querySelectorAll('#webhookFormContainer input[type="checkbox"]').forEach(cb => {
            cb.checked = webhook.events.includes(cb.value);
        });
        document.getElementById('webhookActive').checked = webhook.is_active;
        editingWebhookId = webhook.id;
    } else {
        document.getElementById('webhookId').value = '';
        document.getElementById('webhookName').value = '';
        document.getElementById('webhookUrl').value = '';
        document.getElementById('webhookSecret').value = '';
        document.querySelectorAll('#webhookFormContainer input[type="checkbox"]').forEach(cb => cb.checked = false);
        document.getElementById('webhookActive').checked = true;
        editingWebhookId = null;
    }
    form.style.display = 'block';
}

document.getElementById('addWebhookBtn').addEventListener('click', () => showWebhookForm());

document.getElementById('cancelWebhookBtn').addEventListener('click', () => {
    document.getElementById('webhookFormContainer').style.display = 'none';
});

window.editWebhook = async function(id) {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`/integration/webhooks/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch');
        const webhook = await response.json();
        showWebhookForm(webhook);
    } catch (error) {
        showAlert('Could not load webhook details', 'error');
    }
};

window.deleteWebhook = async function(id) {
    if (!confirm('Delete this webhook?')) return;
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`/integration/webhooks/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (response.ok) {
            showAlert('Webhook deleted', 'success');
            loadWebhooks();
            loadStatus();
        } else {
            const err = await response.json();
            showAlert(err.detail || 'Failed', 'error');
        }
    } catch (error) {
        showAlert('Network error', 'error');
    }
};

document.getElementById('saveWebhookBtn').addEventListener('click', async () => {
    const name = document.getElementById('webhookName').value.trim();
    const url = document.getElementById('webhookUrl').value.trim();
    const secret = document.getElementById('webhookSecret').value.trim() || null;
    const active = document.getElementById('webhookActive').checked;
    const events = [];
    document.querySelectorAll('#webhookFormContainer input[type="checkbox"]:checked').forEach(cb => {
        events.push(cb.value);
    });

    if (!name || !url || events.length === 0) {
        showAlert('Name, URL, and at least one event are required', 'error');
        return;
    }

    const token = localStorage.getItem('access_token');
    const method = editingWebhookId ? 'PUT' : 'POST';
    const urlPath = editingWebhookId ? `/integration/webhooks/${editingWebhookId}` : '/integration/webhooks';

    try {
        const response = await fetch(urlPath, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                name,
                url,
                secret,
                events,
                is_active: active
            })
        });

        if (response.ok) {
            showAlert(editingWebhookId ? 'Webhook updated' : 'Webhook created', 'success');
            document.getElementById('webhookFormContainer').style.display = 'none';
            loadWebhooks();
            loadStatus();
        } else {
            const err = await response.json();
            showAlert(err.detail || 'Save failed', 'error');
        }
    } catch (error) {
        showAlert('Network error', 'error');
    }
});

// ---------- STATUS & DELIVERIES ----------
async function loadStatus() {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch('/integration/status', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error();
        const status = await response.json();
        document.getElementById('totalApiKeys').textContent = status.total_api_keys;
        document.getElementById('activeApiKeys').textContent = status.active_api_keys;
        document.getElementById('totalWebhooks').textContent = status.total_webhooks;
        document.getElementById('activeWebhooks').textContent = status.active_webhooks;
    } catch (error) {
        // ignore
    }
}

async function loadDeliveries() {
    const token = localStorage.getItem('access_token');
    const listDiv = document.getElementById('deliveriesList');
    try {
        const response = await fetch('/integration/status');  // same endpoint includes recent deliveries
        if (!response.ok) throw new Error();
        const status = await response.json();
        const deliveries = status.recent_deliveries || [];
        if (deliveries.length === 0) {
            listDiv.innerHTML = '<p class="text-muted">No recent webhook deliveries.</p>';
            return;
        }
        let html = '<table class="table"><tr><th>Time</th><th>Webhook</th><th>Event</th><th>Status</th></tr>';
        deliveries.forEach(d => {
            const statusClass = d.success ? 'badge-success' : 'badge-danger';
            html += `<tr>
                <td>${new Date(d.attempted_at).toLocaleString()}</td>
                <td>${d.webhook_name || d.webhook_id}</td>
                <td>${d.event}</td>
                <td><span class="badge ${statusClass}">${d.success ? 'Success' : 'Failed'} (${d.response_status || '??'})</span></td>
            </tr>`;
        });
        html += '</table>';
        listDiv.innerHTML = html;
    } catch (error) {
        listDiv.innerHTML = '<p class="alert alert-error">Error loading deliveries.</p>';
    }
}

// ---------- ALERT HELPER ----------
function showAlert(message, type = 'success') {
    const alertDiv = document.getElementById('alert');
    alertDiv.style.display = 'block';
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    setTimeout(() => alertDiv.style.display = 'none', 3000);
}