// frontend/js/admin.js

// ---------- AUTH CHECK – ADMIN ONLY ----------
(async function() {
    const user = await checkAuth(['admin']); // strict admin only
    if (!user) return;
    window.currentUser = user;
    initTabs();
    loadUsers(); // default tab
})();

// ---------- LOGOUT ----------
document.getElementById('logoutLink').addEventListener('click', (e) => {
    e.preventDefault();
    logout();
});

// ---------- TAB SWITCHING ----------
function initTabs() {
    const tabs = document.querySelectorAll('.admin-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const tabName = tab.dataset.tab;
            showTab(tabName);
        });
    });
}

function showTab(tabName) {
    // Hide all tab content
    document.getElementById('users-tab').style.display = 'none';
    document.getElementById('settings-tab').style.display = 'none';
    document.getElementById('categories-tab').style.display = 'none';
    document.getElementById('movement-types-tab').style.display = 'none';
    document.getElementById('audit-tab').style.display = 'none';

    // Show selected tab
    document.getElementById(`${tabName}-tab`).style.display = 'block';

    // Load data if needed
    if (tabName === 'settings') loadSettings();
    if (tabName === 'categories') loadCategories();
    if (tabName === 'movement-types') loadMovementTypes();
    if (tabName === 'audit') loadAuditLogs();
}

// ---------- ALERT HELPER ----------
function showAlert(message, type = 'success') {
    const alertDiv = document.getElementById('alert');
    alertDiv.style.display = 'block';
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    setTimeout(() => alertDiv.style.display = 'none', 3000);
}

// ---------- USERS ----------
let editingUserId = null;

async function loadUsers() {
    const token = localStorage.getItem('access_token');
    const tbody = document.getElementById('usersList');
    try {
        const res = await fetch('/admin/users', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed');
        const users = await res.json();
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7">No users found.</td></tr>';
            return;
        }
        let html = '';
        users.forEach(u => {
            const role = u.roles ? u.roles.split(',')[0] : 'clerk';
            html += `<tr>
                <td>${u.id}</td>
                <td>${u.username}</td>
                <td>${u.email}</td>
                <td>${role}</td>
                <td>${u.is_active ? '✅' : '❌'}</td>
                <td>${new Date(u.created_at).toLocaleDateString()}</td>
                <td>
                    <button onclick="editUser(${u.id})" class="btn" style="padding:5px 10px;">Edit</button>
                    <button onclick="deleteUser(${u.id})" class="btn btn-danger" style="padding:5px 10px;">Delete</button>
                </td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="7" class="alert alert-error">Error loading users.</td></tr>';
    }
}

function showUserForm(user = null) {
    const form = document.getElementById('userFormContainer');
    document.getElementById('userFormTitle').textContent = user ? 'Edit User' : 'Add User';
    if (user) {
        document.getElementById('editUserId').value = user.id;
        document.getElementById('username').value = user.username;
        document.getElementById('email').value = user.email;
        document.getElementById('password').value = ''; // leave blank
        document.getElementById('role').value = (user.roles ? user.roles.split(',')[0] : 'clerk');
        document.getElementById('isActive').checked = user.is_active;
        editingUserId = user.id;
    } else {
        document.getElementById('editUserId').value = '';
        document.getElementById('username').value = '';
        document.getElementById('email').value = '';
        document.getElementById('password').value = '';
        document.getElementById('role').value = 'clerk';
        document.getElementById('isActive').checked = true;
        editingUserId = null;
    }
    form.style.display = 'block';
}

document.getElementById('addUserBtn').addEventListener('click', () => showUserForm());

document.getElementById('cancelUserBtn').addEventListener('click', () => {
    document.getElementById('userFormContainer').style.display = 'none';
});

document.getElementById('saveUserBtn').addEventListener('click', async () => {
    const token = localStorage.getItem('access_token');
    const userData = {
        username: document.getElementById('username').value.trim(),
        email: document.getElementById('email').value.trim(),
        password: document.getElementById('password').value,
        role: document.getElementById('role').value,
        is_active: document.getElementById('isActive').checked
    };
    if (!userData.username || !userData.email) {
        showAlert('Username and email are required', 'error');
        return;
    }
    if (!editingUserId && !userData.password) {
        showAlert('Password is required for new users', 'error');
        return;
    }
    const url = editingUserId ? `/admin/users/${editingUserId}` : '/admin/users';
    const method = editingUserId ? 'PUT' : 'POST';
    try {
        const res = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(userData)
        });
        if (res.ok) {
            showAlert(editingUserId ? 'User updated' : 'User created', 'success');
            document.getElementById('userFormContainer').style.display = 'none';
            loadUsers();
        } else {
            const err = await res.json();
            showAlert(err.detail || 'Save failed', 'error');
        }
    } catch (e) {
        showAlert('Network error', 'error');
    }
});

window.editUser = async function(id) {
    const token = localStorage.getItem('access_token');
    try {
        const res = await fetch(`/admin/users/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error();
        const user = await res.json();
        showUserForm(user);
    } catch (e) {
        showAlert('Could not load user', 'error');
    }
};

window.deleteUser = async function(id) {
    if (!confirm('Delete this user? They will be deactivated.')) return;
    const token = localStorage.getItem('access_token');
    try {
        const res = await fetch(`/admin/users/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            showAlert('User deactivated', 'success');
            loadUsers();
        } else {
            const err = await res.json();
            showAlert(err.detail || 'Delete failed', 'error');
        }
    } catch (e) {
        showAlert('Network error', 'error');
    }
};

// ---------- SETTINGS ----------
async function loadSettings() {
    const token = localStorage.getItem('access_token');
    const tbody = document.getElementById('settingsList');
    try {
        const res = await fetch('/admin/settings', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error();
        const settings = await res.json();
        if (settings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No settings found.</td></tr>';
            return;
        }
        let html = '';
        settings.forEach(s => {
            html += `<tr>
                <td><strong>${s.key}</strong></td>
                <td>
                    <input type="text" id="set_${s.key}" value="${s.value}" class="form-control" style="width:200px;">
                </td>
                <td>${s.description || ''}</td>
                <td>${s.updated_by_username || ''}<br><small>${new Date(s.updated_at).toLocaleString()}</small></td>
                <td>
                    <button onclick="updateSetting('${s.key}')" class="btn" style="padding:5px 10px;">Update</button>
                </td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" class="alert alert-error">Error loading settings.</td></tr>';
    }
}

window.updateSetting = async function(key) {
    const value = document.getElementById(`set_${key}`).value.trim();
    const token = localStorage.getItem('access_token');
    try {
        const res = await fetch(`/admin/settings/${key}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ value })
        });
        if (res.ok) {
            showAlert('Setting updated', 'success');
        } else {
            const err = await res.json();
            showAlert(err.detail || 'Update failed', 'error');
        }
    } catch (e) {
        showAlert('Network error', 'error');
    }
};

// ---------- CATEGORIES ----------
let editingCategoryId = null;

async function loadCategories() {
    const token = localStorage.getItem('access_token');
    const tbody = document.getElementById('categoriesList');
    try {
        const res = await fetch('/admin/categories', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error();
        const cats = await res.json();
        if (cats.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No categories found.</td></tr>';
            return;
        }
        let html = '';
        cats.forEach(c => {
            html += `<tr>
                <td>${c.id}</td>
                <td>${c.name}</td>
                <td>${c.description || ''}</td>
                <td>${new Date(c.created_at).toLocaleDateString()}</td>
                <td>
                    <button onclick="editCategory(${c.id}, '${c.name}', '${c.description || ''}')" class="btn" style="padding:5px 10px;">Edit</button>
                    <button onclick="deleteCategory(${c.id})" class="btn btn-danger" style="padding:5px 10px;">Delete</button>
                </td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" class="alert alert-error">Error loading categories.</td></tr>';
    }
}

function showCategoryForm(cat = null) {
    const form = document.getElementById('categoryFormContainer');
    document.getElementById('categoryFormTitle').textContent = cat ? 'Edit Category' : 'Add Category';
    if (cat) {
        document.getElementById('editCategoryId').value = cat.id;
        document.getElementById('categoryName').value = cat.name;
        document.getElementById('categoryDesc').value = cat.description || '';
        editingCategoryId = cat.id;
    } else {
        document.getElementById('editCategoryId').value = '';
        document.getElementById('categoryName').value = '';
        document.getElementById('categoryDesc').value = '';
        editingCategoryId = null;
    }
    form.style.display = 'block';
}

document.getElementById('addCategoryBtn').addEventListener('click', () => showCategoryForm());

document.getElementById('cancelCategoryBtn').addEventListener('click', () => {
    document.getElementById('categoryFormContainer').style.display = 'none';
});

document.getElementById('saveCategoryBtn').addEventListener('click', async () => {
    const name = document.getElementById('categoryName').value.trim();
    const desc = document.getElementById('categoryDesc').value.trim() || null;
    if (!name) {
        showAlert('Name is required', 'error');
        return;
    }
    const token = localStorage.getItem('access_token');
    const url = editingCategoryId ? `/admin/categories/${editingCategoryId}` : '/admin/categories';
    const method = editingCategoryId ? 'PUT' : 'POST';
    try {
        const res = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ name, description: desc })
        });
        if (res.ok) {
            showAlert(editingCategoryId ? 'Category updated' : 'Category added', 'success');
            document.getElementById('categoryFormContainer').style.display = 'none';
            loadCategories();
        } else {
            const err = await res.json();
            showAlert(err.detail || 'Save failed', 'error');
        }
    } catch (e) {
        showAlert('Network error', 'error');
    }
});

window.editCategory = function(id, name, desc) {
    showCategoryForm({ id, name, description: desc });
};

window.deleteCategory = async function(id) {
    if (!confirm('Delete this category? Cannot delete if used by products.')) return;
    const token = localStorage.getItem('access_token');
    try {
        const res = await fetch(`/admin/categories/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            showAlert('Category deleted', 'success');
            loadCategories();
        } else {
            const err = await res.json();
            showAlert(err.detail || 'Delete failed', 'error');
        }
    } catch (e) {
        showAlert('Network error', 'error');
    }
};

// ---------- MOVEMENT TYPES ----------
let editingMovementTypeId = null;

async function loadMovementTypes() {
    const token = localStorage.getItem('access_token');
    const tbody = document.getElementById('movementTypesList');
    try {
        const res = await fetch('/admin/movement-types', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error();
        const types = await res.json();
        if (types.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No movement types found.</td></tr>';
            return;
        }
        let html = '';
        types.forEach(t => {
            html += `<tr>
                <td>${t.id}</td>
                <td>${t.name}</td>
                <td>${t.description || ''}</td>
                <td>${t.sign === 1 ? '+' : '-'}</td>
                <td>
                    <button onclick="editMovementType(${t.id}, '${t.name}', '${t.description || ''}', ${t.sign})" class="btn" style="padding:5px 10px;">Edit</button>
                    <button onclick="deleteMovementType(${t.id})" class="btn btn-danger" style="padding:5px 10px;">Delete</button>
                </td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" class="alert alert-error">Error loading movement types.</td></tr>';
    }
}

function showMovementTypeForm(type = null) {
    const form = document.getElementById('movementTypeFormContainer');
    document.getElementById('movementTypeFormTitle').textContent = type ? 'Edit Movement Type' : 'Add Movement Type';
    if (type) {
        document.getElementById('editMovementTypeId').value = type.id;
        document.getElementById('movementTypeName').value = type.name;
        document.getElementById('movementTypeDesc').value = type.description || '';
        document.getElementById('movementTypeSign').value = type.sign;
        editingMovementTypeId = type.id;
    } else {
        document.getElementById('editMovementTypeId').value = '';
        document.getElementById('movementTypeName').value = '';
        document.getElementById('movementTypeDesc').value = '';
        document.getElementById('movementTypeSign').value = '1';
        editingMovementTypeId = null;
    }
    form.style.display = 'block';
}

document.getElementById('addMovementTypeBtn').addEventListener('click', () => showMovementTypeForm());

document.getElementById('cancelMovementTypeBtn').addEventListener('click', () => {
    document.getElementById('movementTypeFormContainer').style.display = 'none';
});

document.getElementById('saveMovementTypeBtn').addEventListener('click', async () => {
    const name = document.getElementById('movementTypeName').value.trim();
    const desc = document.getElementById('movementTypeDesc').value.trim() || null;
    const sign = parseInt(document.getElementById('movementTypeSign').value);
    if (!name) {
        showAlert('Name is required', 'error');
        return;
    }
    const token = localStorage.getItem('access_token');
    const url = editingMovementTypeId ? `/admin/movement-types/${editingMovementTypeId}` : '/admin/movement-types';
    const method = editingMovementTypeId ? 'PUT' : 'POST';
    try {
        const res = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ name, description: desc, sign })
        });
        if (res.ok) {
            showAlert(editingMovementTypeId ? 'Movement type updated' : 'Movement type added', 'success');
            document.getElementById('movementTypeFormContainer').style.display = 'none';
            loadMovementTypes();
        } else {
            const err = await res.json();
            showAlert(err.detail || 'Save failed', 'error');
        }
    } catch (e) {
        showAlert('Network error', 'error');
    }
});

window.editMovementType = function(id, name, desc, sign) {
    showMovementTypeForm({ id, name, description: desc, sign });
};

window.deleteMovementType = async function(id) {
    if (!confirm('Delete this movement type? Cannot delete if used in stock movements.')) return;
    const token = localStorage.getItem('access_token');
    try {
        const res = await fetch(`/admin/movement-types/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            showAlert('Movement type deleted', 'success');
            loadMovementTypes();
        } else {
            const err = await res.json();
            showAlert(err.detail || 'Delete failed', 'error');
        }
    } catch (e) {
        showAlert('Network error', 'error');
    }
};

// ---------- AUDIT LOG ----------
async function loadAuditLogs() {
    const token = localStorage.getItem('access_token');
    const tbody = document.getElementById('auditList');
    const table = document.getElementById('filterTable').value;
    const user = document.getElementById('filterUser').value;
    const from = document.getElementById('filterFrom').value;
    const to = document.getElementById('filterTo').value;
    const op = document.getElementById('filterOperation').value;

    let url = '/admin/audit-logs?';
    if (table) url += `&table_name=${table}`;
    if (user) url += `&user_id=${user}`;
    if (from) url += `&from_date=${from}`;
    if (to) url += `&to_date=${to}`;
    if (op) url += `&operation=${op}`;

    try {
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error();
        const logs = await res.json();
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No audit logs found.</td></tr>';
            return;
        }
        let html = '';
        logs.forEach(l => {
            let changes = '';
            if (l.operation === 'UPDATE' && l.old_data && l.new_data) {
                changes = 'Updated';
            } else if (l.operation === 'INSERT') {
                changes = 'Inserted';
            } else if (l.operation === 'DELETE') {
                changes = 'Deleted';
            }
            html += `<tr>
                <td>${new Date(l.changed_at).toLocaleString()}</td>
                <td>${l.table_name}</td>
                <td>${l.operation}</td>
                <td>${l.record_id}</td>
                <td>${l.changed_by_username || l.changed_by || 'system'}</td>
                <td>${changes}</td>
            </tr>`;
        });
        tbody.innerHTML = html;
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6" class="alert alert-error">Error loading audit logs.</td></tr>';
    }
}

document.getElementById('applyAuditFilter').addEventListener('click', loadAuditLogs);