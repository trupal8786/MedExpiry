/**
 * MedExpiry — Dashboard Application Logic
 * Handles: Stats, Alerts, Medicine Table on index.html
 */

const API_BASE = '/api';

// ─────────────────────────────────────
// Initialization
// ─────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    loadAlerts();
    loadMedicineTable();
    initMobileMenu();
});

// ─────────────────────────────────────
// Mobile Menu Toggle
// ─────────────────────────────────────

function initMobileMenu() {
    const btn = document.getElementById('mobileMenuBtn');
    const menu = document.getElementById('mobileMenu');
    if (btn && menu) {
        btn.addEventListener('click', () => {
            menu.classList.toggle('hidden');
        });
    }
}

// ─────────────────────────────────────
// Dashboard Stats
// ─────────────────────────────────────

async function loadDashboard() {
    try {
        const res = await fetch(`${API_BASE}/dashboard`);
        const data = await res.json();

        if (data.success) {
            renderStats(data.stats);
        }
    } catch (err) {
        console.error('Dashboard load failed:', err);
        renderStatsError();
    }
}

function renderStats(stats) {
    const grid = document.getElementById('statsGrid');
    grid.innerHTML = `
        <div class="bg-dark-800/30 rounded-2xl border border-white/5 p-6 hover:border-brand-500/20 transition-colors">
            <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 bg-brand-500/10 rounded-xl flex items-center justify-center text-xl">💊</div>
                <span class="text-sm text-gray-400">Total Medicines</span>
            </div>
            <span class="text-3xl font-display font-bold">${stats.total_medicines}</span>
        </div>
        <div class="bg-dark-800/30 rounded-2xl border border-danger-500/20 p-6 hover:border-danger-500/30 transition-colors">
            <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 bg-danger-500/10 rounded-xl flex items-center justify-center text-xl">⚠️</div>
                <span class="text-sm text-gray-400">Expiring Soon</span>
            </div>
            <span class="text-3xl font-display font-bold text-danger-400">${stats.expiring_this_month}</span>
            <span class="text-xs text-gray-500 ml-2">within 30 days</span>
        </div>
        <div class="bg-dark-800/30 rounded-2xl border border-white/5 p-6 hover:border-red-500/20 transition-colors">
            <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 bg-red-500/10 rounded-xl flex items-center justify-center text-xl">🚫</div>
                <span class="text-sm text-gray-400">Expired</span>
            </div>
            <span class="text-3xl font-display font-bold text-red-400">${stats.expired_count}</span>
            <span class="text-xs text-gray-500 ml-2">≈ ${stats.estimated_waste_value} wasted</span>
        </div>
        <div class="bg-dark-800/30 rounded-2xl border border-white/5 p-6 hover:border-pink-500/20 transition-colors">
            <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 bg-pink-500/10 rounded-xl flex items-center justify-center text-xl">❤️</div>
                <span class="text-sm text-gray-400">Donated</span>
            </div>
            <span class="text-3xl font-display font-bold text-pink-400">${stats.donated_count}</span>
        </div>
    `;
}

function renderStatsError() {
    const grid = document.getElementById('statsGrid');
    grid.innerHTML = `<div class="col-span-full text-center py-8 text-gray-500">
        <p>Unable to load dashboard. Is the server running?</p>
        <p class="text-sm mt-1">Start with: <code class="bg-dark-800 px-2 py-1 rounded text-brand-400">python backend/app.py</code></p>
    </div>`;
}

// ─────────────────────────────────────
// Smart Alerts
// ─────────────────────────────────────

async function loadAlerts() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/alerts`);
        const data = await res.json();

        if (data.success) {
            renderAlerts(data.alerts);
        }
    } catch (err) {
        document.getElementById('alertsList').innerHTML =
            '<p class="text-gray-500 text-sm px-2">Could not load alerts.</p>';
    }
}

function renderAlerts(alerts) {
    const container = document.getElementById('alertsList');

    if (!alerts.length) {
        container.innerHTML = `
            <div class="bg-brand-500/5 border border-brand-500/10 rounded-2xl p-4 text-center">
                <span class="text-2xl">✅</span>
                <p class="text-brand-400 font-medium mt-1">All medicines are in good shape!</p>
            </div>`;
        return;
    }

    container.innerHTML = alerts.slice(0, 5).map(alert => `
        <div class="alert-card alert-${alert.severity}">
            <span class="text-2xl flex-shrink-0">${alert.icon}</span>
            <div class="flex-1 min-w-0">
                <p class="font-semibold text-sm">${alert.title}</p>
                <p class="text-xs text-gray-400 mt-0.5">${alert.message}</p>
            </div>
            ${alert.action === 'use_or_donate'
                ? `<a href="donate.html" class="flex-shrink-0 text-xs bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-lg font-medium transition-colors">Donate</a>`
                : ''}
        </div>
    `).join('');
}

// ─────────────────────────────────────
// Medicine Table
// ─────────────────────────────────────

async function loadMedicineTable() {
    try {
        const res = await fetch(`${API_BASE}/medicines`);
        const data = await res.json();

        if (data.success) {
            renderMedicineTable(data.medicines);
        }
    } catch (err) {
        document.getElementById('medicineTableBody').innerHTML =
            '<tr><td colspan="6" class="px-6 py-12 text-center text-gray-500">Server not reachable. Start the backend.</td></tr>';
    }
}

function renderMedicineTable(medicines) {
    const tbody = document.getElementById('medicineTableBody');

    if (!medicines.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-12 text-center text-gray-500">No medicines yet. Start by scanning one!</td></tr>';
        return;
    }

    tbody.innerHTML = medicines.map(med => `
        <tr class="hover:bg-white/[0.02] transition-colors ${med.status === 'expired' ? 'bg-red-500/[0.02]' : ''}">
            <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-xl bg-gradient-to-br ${getGradient(med.status)} flex items-center justify-center text-sm font-bold text-white">
                        ${med.name.charAt(0)}
                    </div>
                    <div>
                        <p class="font-semibold text-sm ${med.status === 'expired' ? 'line-through text-gray-500' : ''}">${med.name}</p>
                        ${med.batch_number ? `<p class="text-xs text-gray-500">Batch: ${med.batch_number}</p>` : ''}
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 hidden sm:table-cell">
                <span class="text-xs text-gray-400 bg-white/5 px-2 py-1 rounded-lg">${med.category || 'Other'}</span>
            </td>
            <td class="px-6 py-4">
                <p class="text-sm font-medium">${med.expiry_display || 'N/A'}</p>
                <p class="text-xs text-gray-500">${formatDaysUntil(med.days_until_expiry)}</p>
            </td>
            <td class="px-6 py-4 hidden md:table-cell">
                <span class="text-sm">${med.quantity || 0}</span>
            </td>
            <td class="px-6 py-4">
                <span class="status-badge status-${med.status}">${getStatusIcon(med.status)} ${med.status}</span>
            </td>
            <td class="px-6 py-4 text-right">
                <div class="flex items-center justify-end gap-2">
                    ${med.status !== 'expired' ? `
                        <button onclick="consumeMed('${med.id}')" class="p-2 hover:bg-white/5 rounded-lg transition-colors" title="Log consumption">
                            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                        </button>
                    ` : ''}
                    <button onclick="deleteMed('${med.id}')" class="p-2 hover:bg-red-500/10 rounded-lg transition-colors" title="Delete">
                        <svg class="w-4 h-4 text-gray-400 hover:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// ─────────────────────────────────────
// Actions
// ─────────────────────────────────────

async function consumeMed(id) {
    try {
        await fetch(`${API_BASE}/medicines/${id}/consume`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity: 1 })
        });
        showToast('Consumption logged!', 'success');
        loadMedicineTable();
        loadDashboard();
    } catch (err) {
        showToast('Failed to log consumption', 'error');
    }
}

async function deleteMed(id) {
    if (!confirm('Remove this medicine from inventory?')) return;
    try {
        await fetch(`${API_BASE}/medicines/${id}`, { method: 'DELETE' });
        showToast('Medicine removed', 'success');
        loadMedicineTable();
        loadDashboard();
        loadAlerts();
    } catch (err) {
        showToast('Failed to delete', 'error');
    }
}

// ─────────────────────────────────────
// Utilities
// ─────────────────────────────────────

function getGradient(status) {
    const gradients = {
        expired: 'from-red-500 to-red-700',
        critical: 'from-red-400 to-red-600',
        warning: 'from-amber-400 to-amber-600',
        soon: 'from-blue-400 to-blue-600',
        safe: 'from-green-400 to-green-600',
    };
    return gradients[status] || 'from-gray-400 to-gray-600';
}

function getStatusIcon(status) {
    const icons = { expired:'🚫', critical:'🔴', warning:'🟡', soon:'🔵', safe:'🟢' };
    return icons[status] || '⚪';
}

function formatDaysUntil(days) {
    if (days == null) return '';
    if (days < 0) return `Expired ${Math.abs(days)} days ago`;
    if (days === 0) return 'Expires today!';
    if (days === 1) return 'Expires tomorrow';
    return `${days} days left`;
}

function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}
