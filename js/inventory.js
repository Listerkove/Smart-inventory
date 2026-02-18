const token = localStorage.getItem('access_token');
if (!token) window.location.href = 'login.html';

// Logout handler
document.getElementById('logoutLink').addEventListener('click', function(e) {
    e.preventDefault();
    localStorage.removeItem('access_token');
    window.location.href = 'login.html';
});

// Tab switching
const receiptForm = document.getElementById('receiptForm');
const adjustForm = document.getElementById('adjustForm');
const historyView = document.getElementById('historyView');
const tabReceipt = document.getElementById('tabReceipt');
const tabAdjust = document.getElementById('tabAdjust');
const tabHistory = document.getElementById('tabHistory');

function showTab(tab) {
    receiptForm.style.display = 'none';
    adjustForm.style.display = 'none';
    historyView.style.display = 'none';
    
    if (tab === 'receipt') {
        receiptForm.style.display = 'block';
    } else if (tab === 'adjust') {
        adjustForm.style.display = 'block';
    } else if (tab === 'history') {
        historyView.style.display = 'block';
        loadMovements();
    }
}

tabReceipt.addEventListener('click', () => showTab('receipt'));
tabAdjust.addEventListener('click', () => showTab('adjust'));
tabHistory.addEventListener('click', () => showTab('history'));

// Stock Receipt
document.getElementById('receiptFormElement').addEventListener('submit', async function(e) {
    e.preventDefault();
    const sku = document.getElementById('receipt_sku').value.trim();
    const quantity = parseInt(document.getElementById('receipt_quantity').value);
    const reference_id = document.getElementById('receipt_reference').value.trim() || null;
    const alertDiv = document.getElementById('alert');

    alertDiv.style.display = 'none';
    alertDiv.className = 'alert';

    try {
        const response = await fetch('/inventory/receipt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ product_sku: sku, quantity, reference_id })
        });

        const data = await response.json();

        if (response.ok) {
            alertDiv.style.display = 'block';
            alertDiv.className = 'alert alert-success';
            alertDiv.textContent = `✅ Stock received. New quantity: ${data.new_quantity}`;
            document.getElementById('receiptFormElement').reset();
        } else {
            alertDiv.style.display = 'block';
            alertDiv.className = 'alert alert-error';
            alertDiv.textContent = data.detail || 'Failed to receive stock';
        }
    } catch (error) {
        console.error(error);
        alertDiv.style.display = 'block';
        alertDiv.className = 'alert alert-error';
        alertDiv.textContent = 'Network error. Please try again.';
    }
});

// Stock Adjustment
document.getElementById('adjustFormElement').addEventListener('submit', async function(e) {
    e.preventDefault();
    const sku = document.getElementById('adjust_sku').value.trim();
    const movement_type = document.getElementById('adjust_type').value;
    const quantity = parseInt(document.getElementById('adjust_quantity').value);
    const reason = document.getElementById('adjust_reason').value.trim();
    const alertDiv = document.getElementById('alert');

    alertDiv.style.display = 'none';
    alertDiv.className = 'alert';

    try {
        const response = await fetch('/inventory/adjust', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                product_sku: sku,
                movement_type,
                quantity,
                reason
            })
        });

        const data = await response.json();

        if (response.ok) {
            alertDiv.style.display = 'block';
            alertDiv.className = 'alert alert-success';
            alertDiv.textContent = `✅ Adjustment recorded. New quantity: ${data.new_quantity}`;
            document.getElementById('adjustFormElement').reset();
        } else {
            alertDiv.style.display = 'block';
            alertDiv.className = 'alert alert-error';
            alertDiv.textContent = data.detail || 'Failed to record adjustment';
        }
    } catch (error) {
        console.error(error);
        alertDiv.style.display = 'block';
        alertDiv.className = 'alert alert-error';
        alertDiv.textContent = 'Network error. Please try again.';
    }
});

// Load movement history
async function loadMovements(skuFilter = '') {
    const tbody = document.getElementById('movementList');
    tbody.innerHTML = '<tr><td colspan="10" class="text-center">Loading...</td></tr>';
    
    let url = '/inventory/movements?limit=200';
    if (skuFilter) url += `&product_sku=${encodeURIComponent(skuFilter)}`;

    try {
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to load movements');
        
        const movements = await response.json();
        
        if (movements.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center">No movements found.</td></tr>';
            return;
        }

        let html = '';
        movements.forEach(m => {
            const date = new Date(m.created_at).toLocaleString();
            const sign = m.movement_type === 'sale' || m.movement_type === 'damage' ? '-' : '+';
            html += `<tr>
                <td>${date}</td>
                <td>${m.product_name || '-'}</td>
                <td>${m.product_sku}</td>
                <td>${m.movement_type}</td>
                <td>${sign}${m.quantity}</td>
                <td>${m.previous_quantity}</td>
                <td>${m.new_quantity}</td>
                <td>${m.reference_id || '-'}</td>
                <td>${m.reason || '-'}</td>
                <td>${m.performed_by || 'system'}</td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (error) {
        console.error(error);
        tbody.innerHTML = '<tr><td colspan="10" class="text-center alert alert-error">Error loading movements.</td></tr>';
    }
}

// Filter button
document.getElementById('applyFilter')?.addEventListener('click', function() {
    const sku = document.getElementById('filter_sku').value.trim();
    loadMovements(sku);
});

// Reset filter
document.getElementById('resetFilter')?.addEventListener('click', function() {
    document.getElementById('filter_sku').value = '';
    loadMovements('');
});