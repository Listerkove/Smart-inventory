// auth.js – role-based redirects

const API_BASE = '';  // relative URLs

async function checkAuth(allowedRoles = ['manager', 'admin']) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'login.html';
        return null;
    }

    try {
        const response = await fetch('/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Not authenticated');

        const user = await response.json();
        
        // user.roles is comma-separated string, e.g. "admin,manager"
        const roles = user.roles ? user.roles.split(',') : [];
        const hasAccess = allowedRoles.some(role => roles.includes(role));

        if (!hasAccess) {
            // Redirect to dashboard with error message
            window.location.href = 'dashboard.html?error=unauthorized';
            return null;
        }

        return user;
    } catch (error) {
        localStorage.removeItem('access_token');
        window.location.href = 'login.html';
        return null;
    }
}

// For pages that need to display user info
async function getUserInfo() {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    try {
        const res = await fetch('/auth/me', { headers: { 'Authorization': `Bearer ${token}` } });
        if (!res.ok) throw new Error();
        return await res.json();
    } catch {
        return null;
    }
}

// Logout helper
function logout() {
    localStorage.removeItem('access_token');
    window.location.href = 'login.html';
}