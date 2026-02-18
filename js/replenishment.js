// frontend/js/replenishment.js

// ---------- AUTH CHECK – MANAGER/ADMIN ONLY ----------
(async function() {
    const user = await checkAuth(['manager', 'admin']);
    if (!user) return;
    window.currentUser = user;
    
    // Load initial suggestions (active only)
    loadSuggestions(true);
})();

// ---------- LOGOUT ----------
document.getElementById('logoutLink').addEventListener('click', function(e) {
    e.preventDefault();
    logout();
});

// ---------- UI HELPERS ----------
function showAlert(message, type = 'success') {
    const alertDiv = document.getElementById('alert');
    alertDiv.style.display = 'block';
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    setTimeout(() => {
        alertDiv.style.display = 'none';
    }, 3000);
}

// ---------- GENERATE SUGGESTIONS ----------
document.getElementById('generateBtn').addEventListener('click', async function() {
    const lookback = document.getElementById('lookbackDays').value || 30;
    const forecast = document.getElementById('forecastDays').value || 7;
    const safety = document.getElementById('safetyFactor').value || 1.5;
    
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch(`/replenishment/generate?lookback_days=${lookback}&forecast_days=${forecast}&safety_stock_factor=${safety}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('✅ Suggestions generated successfully!', 'success');
            loadSuggestions(true);  // reload active suggestions
        } else {
            showAlert(data.detail || 'Generation failed', 'error');
        }
    } catch (error) {
        console.error(error);
        showAlert('Network error. Please try again.', 'error');
    }
});

// ---------- LOAD SUGGESTIONS ----------
let activeOnly = true;

async function loadSuggestions(active = true) {
    activeOnly = active;
    const token = localStorage.getItem('access_token');
    const listDiv = document.getElementById('suggestionsList');
    
    try {
        const response = await fetch(`/replenishment/suggestions?active_only=${active}&limit=100`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) throw new Error('Failed to load suggestions');
        
        const suggestions = await response.json();
        
        if (suggestions.length === 0) {
            listDiv.innerHTML = '<p style="text-align: center; color: #999; padding: 40px;">No replenishment suggestions found. Generate new ones.</p>';
            return;
        }
        
        let html = '';
        suggestions.forEach(s => {
            const shortage = Math.max(0, s.forecasted_demand - s.current_stock);
            const confidence = shortage <= s.suggested_quantity ? 'high' : 'medium';
            
            html += `
                <div class="suggestion-card ${s.is_acted_upon ? 'accepted' : ''}">
                    <div style="flex:2;">
                        <h3 style="margin:0;">${s.product_name}</h3>
                        <div style="display: flex; gap: 20px; margin-top: 5px;">
                            <span style="font-size:14px; color:#666;">SKU: ${s.product_sku}</span>
                            <span style="font-size:14px; color:#666;">Barcode: ${s.product_barcode || '-'}</span>
                        </div>
                        <div class="forecast-detail">
                            <div><strong>Forecasted Demand:</strong> ${s.forecasted_demand} units</div>
                            <div><strong>Current Stock:</strong> ${s.current_stock}</div>
                            <div><strong>Suggested Order:</strong> <span style="color:#28a745; font-weight:bold;">${s.suggested_quantity}</span></div>
                        </div>
                        <div style="margin-top:10px; font-size:13px; color:#999;">
                            Generated: ${new Date(s.date_generated).toLocaleDateString()}
                            ${s.is_acted_upon ? ` | Acted upon: ${new Date(s.acted_upon_at).toLocaleString()}` : ''}
                        </div>
                    </div>
                    ${!s.is_acted_upon ? `
                    <div class="action-buttons">
                        <button onclick="acceptSuggestion(${s.id})" class="btn btn-success" style="padding:8px 16px;">✓ Accept</button>
                        <button onclick="ignoreSuggestion(${s.id})" class="btn" style="background:#6c757d; padding:8px 16px;">✗ Ignore</button>
                    </div>
                    ` : ''}
                </div>
            `;
        });
        listDiv.innerHTML = html;
    } catch (error) {
        console.error(error);
        listDiv.innerHTML = '<p style="color: #dc3545; text-align: center;">Error loading suggestions.</p>';
    }
}

// ---------- ACCEPT SUGGESTION ----------
window.acceptSuggestion = async function(suggestionId) {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch('/replenishment/actions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                suggestion_id: suggestionId,
                action: 'accept'
            })
        });
        
        if (response.ok) {
            showAlert('✅ Suggestion accepted – stock order recorded', 'success');
            loadSuggestions(activeOnly);
        } else {
            const err = await response.json();
            showAlert(err.detail || 'Action failed', 'error');
        }
    } catch (error) {
        console.error(error);
        showAlert('Network error', 'error');
    }
};

// ---------- IGNORE SUGGESTION ----------
window.ignoreSuggestion = async function(suggestionId) {
    if (!confirm('Are you sure you want to ignore this suggestion?')) return;
    
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch('/replenishment/actions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                suggestion_id: suggestionId,
                action: 'ignore'
            })
        });
        
        if (response.ok) {
            showAlert('Suggestion ignored', 'success');
            loadSuggestions(activeOnly);
        } else {
            const err = await response.json();
            showAlert(err.detail || 'Action failed', 'error');
        }
    } catch (error) {
        console.error(error);
        showAlert('Network error', 'error');
    }
};

// ---------- FILTER TOGGLE ----------
document.getElementById('showActiveBtn').addEventListener('click', function() {
    this.style.background = '#007bff';
    document.getElementById('showAllBtn').style.background = '#6c757d';
    loadSuggestions(true);
});

document.getElementById('showAllBtn').addEventListener('click', function() {
    this.style.background = '#007bff';
    document.getElementById('showActiveBtn').style.background = '#6c757d';
    loadSuggestions(false);
});