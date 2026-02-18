// frontend/js/dashboard.js

let topProductsChart = null;

// ---------- INIT ----------
(async function() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    const user = await getUserInfo();
    if (!user) {
        window.location.href = 'login.html';
        return;
    }

    // Display user info
    const roles = user.roles ? user.roles.split(',') : [];
    const roleDisplay = roles[0] || 'clerk';
    document.getElementById('userInfo').innerHTML = `Welcome, <strong>${user.username}</strong> (${roleDisplay})`;

    // Role-based UI: hide low stock section for clerks
    const isManager = roles.includes('manager') || roles.includes('admin');
    const lowStockSection = document.getElementById('lowStockSection');
    if (lowStockSection) {
        lowStockSection.style.display = isManager ? 'block' : 'none';
    }

    // Hide inventory link in navbar (already handled by individual pages, but do it here too)
    const inventoryLink = document.querySelector('a[href="inventory.html"]');
    if (inventoryLink) {
        inventoryLink.style.display = isManager ? 'block' : 'none';
    }

    // Load all dashboard data
    await loadDashboardSummary();
    await loadLowStockAlerts();
    await loadDailySales();
    await loadTopProducts();
})();

// ---------- LOGOUT ----------
document.getElementById('logoutLink').addEventListener('click', function(e) {
    e.preventDefault();
    logout();
});

// ---------- LOAD SUMMARY METRICS ----------
async function loadDashboardSummary() {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch('/dashboard/summary', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to load summary');
        
        const data = await response.json();
        
        document.getElementById('totalProducts').textContent = data.total_products;
        document.getElementById('stockValue').textContent = Number(data.total_stock_value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
        document.getElementById('lowStockCount').textContent = data.low_stock_count;
        document.getElementById('outOfStockCount').textContent = data.out_of_stock_count;
    } catch (error) {
        console.error('Summary error:', error);
    }
}

// ---------- LOAD LOW STOCK ALERTS ----------
async function loadLowStockAlerts() {
    const token = localStorage.getItem('access_token');
    const lowStockList = document.getElementById('lowStockList');
    
    try {
        const response = await fetch('/dashboard/low-stock', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to load low stock alerts');
        
        const alerts = await response.json();
        
        if (alerts.length === 0) {
            lowStockList.innerHTML = '<p style="color: #28a745;">✅ All stock levels are healthy.</p>';
            return;
        }

        let html = '<table class="low-stock-table">';
        alerts.forEach(item => {
            const badgeClass = item.quantity_in_stock === 0 ? 'badge-danger' : 'badge-warning';
            const status = item.quantity_in_stock === 0 ? 'Out of Stock' : 'Low Stock';
            html += `<tr>
                <td><strong>${item.name}</strong><br><small>SKU: ${item.sku}</small></td>
                <td style="text-align: right;">
                    <span class="badge ${badgeClass}">${item.quantity_in_stock} / ${item.reorder_threshold}</span><br>
                    <small>${status}</small>
                </td>
            </tr>`;
        });
        html += '</table>';
        lowStockList.innerHTML = html;
    } catch (error) {
        console.error('Low stock error:', error);
        lowStockList.innerHTML = '<p style="color: #dc3545;">Error loading alerts.</p>';
    }
}

// ---------- LOAD TODAY'S SALES ----------
async function loadDailySales() {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch('/dashboard/daily-sales', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to load daily sales');
        
        const data = await response.json();
        
        if (data) {
            document.getElementById('todayTransactions').textContent = data.transaction_count || 0;
            document.getElementById('todayItems').textContent = data.total_items_sold || 0;
            document.getElementById('todayRevenue').textContent = Number(data.total_revenue || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
        } else {
            document.getElementById('todayTransactions').textContent = '0';
            document.getElementById('todayItems').textContent = '0';
            document.getElementById('todayRevenue').textContent = '0.00';
        }
    } catch (error) {
        console.error('Daily sales error:', error);
    }
}

// ---------- LOAD TOP PRODUCTS CHART ----------
async function loadTopProducts() {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch('/dashboard/product-performance', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to load product performance');
        
        const products = await response.json();
        
        // Take top 5 best sellers
        const top5 = products.slice(0, 5);
        const labels = top5.map(p => p.name.length > 20 ? p.name.substring(0, 18) + '...' : p.name);
        const data = top5.map(p => p.total_sold_30d);
        
        const ctx = document.getElementById('topProductsChart').getContext('2d');
        
        // Destroy previous chart if exists
        if (topProductsChart) {
            topProductsChart.destroy();
        }
        
        topProductsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Units Sold (30 days)',
                    data: data,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Product performance error:', error);
    }
}

// ---------- AUTO-REFRESH EVERY 60 SECONDS ----------
setInterval(async () => {
    await loadDashboardSummary();
    await loadLowStockAlerts();
    await loadDailySales();
    // Chart will reload on next full refresh, but we can optionally refresh data
}, 60000);