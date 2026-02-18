// frontend/js/reports.js

// ---------- GLOBAL STATE ----------
let currentReport = 'sales';
let chartInstance = null;
let filterOptions = {
    products: [],
    movementTypes: []
};

// ---------- AUTH CHECK ----------
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
    window.currentUser = user;

    // Load filter options
    await loadFilterOptions();
    // Set up initial filter panel
    updateFilterPanel('sales');
    // Load initial data (last 7 days sales)
    loadReportData();
})();

// ---------- LOGOUT ----------
document.getElementById('logoutLink').addEventListener('click', (e) => {
    e.preventDefault();
    logout();
});

// ---------- TAB SWITCHING ----------
document.querySelectorAll('.report-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.report-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentReport = tab.dataset.report;
        updateFilterPanel(currentReport);
        loadReportData();
    });
});

// ---------- LOAD FILTER OPTIONS (products, movement types) ----------
async function loadFilterOptions() {
    const token = localStorage.getItem('access_token');
    try {
        // Products
        const prodRes = await fetch('/reports/filter-options/products', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (prodRes.ok) filterOptions.products = await prodRes.json();

        // Movement types
        const mtRes = await fetch('/reports/filter-options/movement-types', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (mtRes.ok) filterOptions.movementTypes = await mtRes.json();
    } catch (error) {
        console.error('Failed to load filter options', error);
    }
}

// ---------- DYNAMIC FILTER PANEL RENDERING ----------
function updateFilterPanel(reportType) {
    const panel = document.getElementById('filterPanel');
    let html = '';

    if (reportType === 'sales') {
        const today = new Date().toISOString().split('T')[0];
        const lastWeek = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        html = `
            <div class="filter-group">
                <label>From Date</label>
                <input type="date" id="fromDate" value="${lastWeek}">
            </div>
            <div class="filter-group">
                <label>To Date</label>
                <input type="date" id="toDate" value="${today}">
            </div>
            <div class="filter-group">
                <label>Group By</label>
                <select id="groupBy">
                    <option value="day">Day</option>
                    <option value="week">Week</option>
                    <option value="month">Month</option>
                </select>
            </div>
            <button id="applyFilters" class="btn btn-primary">Apply</button>
        `;
    } else if (reportType === 'stock') {
        const today = new Date().toISOString().split('T')[0];
        const lastMonth = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        html = `
            <div class="filter-group">
                <label>From Date</label>
                <input type="date" id="fromDate" value="${lastMonth}">
            </div>
            <div class="filter-group">
                <label>To Date</label>
                <input type="date" id="toDate" value="${today}">
            </div>
            <div class="filter-group">
                <label>Product</label>
                <select id="productSku">
                    <option value="">All Products</option>
                    ${filterOptions.products.map(p => `<option value="${p.sku}">${p.name} (${p.sku})</option>`).join('')}
                </select>
            </div>
            <div class="filter-group">
                <label>Movement Type</label>
                <select id="movementType">
                    <option value="">All Types</option>
                    ${filterOptions.movementTypes.map(t => `<option value="${t}">${t}</option>`).join('')}
                </select>
            </div>
            <button id="applyFilters" class="btn btn-primary">Apply</button>
        `;
    } else if (reportType === 'performance') {
        html = `
            <div class="filter-group">
                <label>Sort By</label>
                <select id="sortBy">
                    <option value="total_sold_30d">Top Sellers (by units)</option>
                    <option value="avg_daily_sales">Avg Daily Sales</option>
                    <option value="stock">Highest Stock</option>
                    <option value="slow_movers">Slow Movers</option>
                    <option value="name">Product Name</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Limit</label>
                <input type="number" id="limit" value="50" min="1" max="500">
            </div>
            <button id="applyFilters" class="btn btn-primary">Apply</button>
        `;
    }

    panel.innerHTML = html;
    document.getElementById('applyFilters')?.addEventListener('click', loadReportData);
}

// ---------- LOAD REPORT DATA FROM API ----------
async function loadReportData() {
    const token = localStorage.getItem('access_token');
    let url = '';
    let params = {};

    if (currentReport === 'sales') {
        const fromDate = document.getElementById('fromDate')?.value;
        const toDate = document.getElementById('toDate')?.value;
        const groupBy = document.getElementById('groupBy')?.value || 'day';
        if (!fromDate || !toDate) return;
        url = `/reports/sales?from_date=${fromDate}&to_date=${toDate}&group_by=${groupBy}`;
    } else if (currentReport === 'stock') {
        const fromDate = document.getElementById('fromDate')?.value;
        const toDate = document.getElementById('toDate')?.value;
        const productSku = document.getElementById('productSku')?.value;
        const movementType = document.getElementById('movementType')?.value;
        url = '/reports/stock-movements?';
        if (fromDate) url += `&from_date=${fromDate}`;
        if (toDate) url += `&to_date=${toDate}`;
        if (productSku) url += `&product_sku=${productSku}`;
        if (movementType) url += `&movement_type=${movementType}`;
        url += '&limit=1000';
    } else if (currentReport === 'performance') {
        const sortBy = document.getElementById('sortBy')?.value || 'total_sold_30d';
        const limit = document.getElementById('limit')?.value || 50;
        url = `/reports/product-performance?sort_by=${sortBy}&limit=${limit}`;
    }

    try {
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to load report');
        const data = await response.json();
        renderReportTable(data);
        renderChart(data);
    } catch (error) {
        console.error(error);
        document.getElementById('tableBody').innerHTML = `<tr><td colspan="10" class="alert alert-error">Error loading report.</td></tr>`;
    }
}

// ---------- RENDER TABLE ----------
function renderReportTable(data) {
    const thead = document.getElementById('tableHeader');
    const tbody = document.getElementById('tableBody');
    
    if (!data || data.length === 0) {
        thead.innerHTML = '<tr><th>No Data</th></tr>';
        tbody.innerHTML = '<tr><td>No records found for selected criteria.</td></tr>';
        return;
    }

    // Get column headers from first object
    const columns = Object.keys(data[0]);
    let headerHtml = '<tr>';
    columns.forEach(col => {
        headerHtml += `<th>${col.replace(/_/g, ' ').toUpperCase()}</th>`;
    });
    headerHtml += '</tr>';
    thead.innerHTML = headerHtml;

    let bodyHtml = '';
    data.forEach(row => {
        bodyHtml += '<tr>';
        columns.forEach(col => {
            let val = row[col];
            if (val === null || val === undefined) val = '-';
            if (col.includes('date') || col.includes('created_at') || col.includes('datetime')) {
                val = new Date(val).toLocaleString();
            }
            if (typeof val === 'number' && (col.includes('price') || col.includes('revenue') || col.includes('value'))) {
                val = 'Ksh ' + val.toFixed(2);
            }
            bodyHtml += `<td>${val}</td>`;
        });
        bodyHtml += '</tr>';
    });
    tbody.innerHTML = bodyHtml;
}

// ---------- RENDER CHART ----------
function renderChart(data) {
    const chartContainer = document.getElementById('chartContainer');
    if (!data || data.length === 0) {
        chartContainer.style.display = 'none';
        return;
    }

    let chartData, chartType, chartLabels, chartValues;

    if (currentReport === 'sales') {
        chartType = 'line';
        chartLabels = data.map(d => d.period);
        chartValues = data.map(d => parseFloat(d.revenue));
        chartData = {
            labels: chartLabels,
            datasets: [{
                label: 'Revenue (Ksh)',
                data: chartValues,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.1
            }]
        };
    } else if (currentReport === 'stock') {
        chartType = 'bar';
        // Group by movement type for simplicity
        const grouped = {};
        data.forEach(d => {
            grouped[d.movement_type] = (grouped[d.movement_type] || 0) + 1;
        });
        chartLabels = Object.keys(grouped);
        chartValues = Object.values(grouped);
        chartData = {
            labels: chartLabels,
            datasets: [{
                label: 'Number of Movements',
                data: chartValues,
                backgroundColor: '#007bff'
            }]
        };
    } else if (currentReport === 'performance') {
        chartType = 'pie';
        const top5 = data.slice(0, 5);
        chartLabels = top5.map(d => d.name.length > 20 ? d.name.substring(0, 18) + '...' : d.name);
        chartValues = top5.map(d => d.total_sold_30d);
        chartData = {
            labels: chartLabels,
            datasets: [{
                label: 'Units Sold (30 days)',
                data: chartValues,
                backgroundColor: ['#28a745', '#ffc107', '#17a2b8', '#dc3545', '#6610f2']
            }]
        };
    }

    if (chartInstance) chartInstance.destroy();
    const ctx = document.getElementById('reportChart').getContext('2d');
    chartInstance = new Chart(ctx, {
        type: chartType,
        data: chartData,
        options: { responsive: true, maintainAspectRatio: false }
    });
    chartContainer.style.display = 'block';
}

// ---------- EXPORT TO CSV ----------
document.getElementById('exportCsvBtn').addEventListener('click', () => {
    const table = document.getElementById('reportTable');
    const rows = table.querySelectorAll('tr');
    let csv = [];
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => `"${col.innerText.replace(/"/g, '""')}"`);
        csv.push(rowData.join(','));
    });
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report_${currentReport}_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
});

// ---------- EXPORT TO PDF (using jsPDF) ----------
document.getElementById('exportPdfBtn').addEventListener('click', () => {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    doc.text(`Smart Inventory - ${currentReport.replace('_',' ').toUpperCase()} Report`, 14, 16);
    doc.setFontSize(10);
    doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 22);
    
    // Use autoTable to generate table from HTML
    doc.autoTable({ html: '#reportTable', startY: 30, theme: 'striped' });
    
    doc.save(`report_${currentReport}_${new Date().toISOString().slice(0,10)}.pdf`);
});