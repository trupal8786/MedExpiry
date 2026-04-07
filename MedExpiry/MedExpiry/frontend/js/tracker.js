/**
 * MedExpiry — Tracker Logic
 * Handles: Inventory grid, Calendar, Filters, AI Predictions
 */

const API_BASE = '/api';
let allMedicines = [];

document.addEventListener('DOMContentLoaded', () => {
    loadInventory();
    loadCalendar();
    loadPredictions();

    document.getElementById('filterStatus').addEventListener('change', applyFilters);
    document.getElementById('filterCategory').addEventListener('change', applyFilters);
});

// ─────────────────────────────────────
// Load Inventory
// ─────────────────────────────────────

async function loadInventory() {
    try {
        const res = await fetch(`${API_BASE}/medicines`);
        const data = await res.json();
        if (data.success) {
            allMedicines = data.medicines;
            renderMedicineGrid(allMedicines);
        }
    } catch (err) {
        document.getElementById('medicineGrid').innerHTML =
            '<p class="text-gray-500 col-span-full text-center py-12">Could not load inventory. Start the backend server.</p>';
    }
}

function renderMedicineGrid(medicines) {
    const grid = document.getElementById('medicineGrid');

    if (!medicines.length) {
        grid.innerHTML = '<p class="text-gray-500 col-span-full text-center py-12">No medicines found. Scan or add one!</p>';
        return;
    }

    grid.innerHTML = medicines.map(med => `
        <div class="medicine-card card-${med.status}">
            <div class="flex items-start justify-between mb-3">
                <div class="flex items-center gap-3">
                    <div class="w-11 h-11 rounded-2xl bg-gradient-to-br ${getGradient(med.status)} flex items-center justify-center text-lg font-bold text-white shadow-lg">
                        ${med.name.charAt(0)}
                    </div>
                    <div>
                        <h3 class="font-semibold ${med.status === 'expired' ? 'line-through text-gray-500' : ''}">${med.name}</h3>
                        <p class="text-xs text-gray-500">${med.category || 'Other'}</p>
                    </div>
                </div>
                <span class="status-badge status-${med.status}">${med.status}</span>
            </div>

            <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                    <span class="text-gray-400">Expiry</span>
                    <span class="font-medium">${med.expiry_display || 'N/A'}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Days Left</span>
                    <span class="font-medium ${med.days_until_expiry < 0 ? 'text-red-400' : med.days_until_expiry <= 30 ? 'text-amber-400' : 'text-green-400'}">
                        ${med.days_until_expiry != null ? (med.days_until_expiry < 0 ? `${Math.abs(med.days_until_expiry)} ago` : med.days_until_expiry) : 'N/A'}
                    </span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Quantity</span>
                    <span class="font-medium">${med.quantity || 0} units</span>
                </div>
                ${med.mrp ? `<div class="flex justify-between"><span class="text-gray-400">MRP</span><span class="font-medium">${med.mrp}</span></div>` : ''}
            </div>

            <div class="flex gap-2 mt-4 pt-3 border-t border-white/5">
                ${med.status !== 'expired' ? `
                    <button onclick="logConsumption('${med.id}')" class="flex-1 py-2 text-xs font-medium bg-white/5 hover:bg-white/10 rounded-xl transition-colors">✅ Take Dose</button>
                ` : ''}
                ${['safe','soon','warning'].includes(med.status) && !med.donated ? `
                    <a href="donate.html" class="flex-1 py-2 text-xs font-medium text-center bg-pink-500/10 hover:bg-pink-500/20 text-pink-400 rounded-xl transition-colors">❤️ Donate</a>
                ` : ''}
                <button onclick="removeMedicine('${med.id}')" class="py-2 px-3 text-xs text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-colors">🗑</button>
            </div>
        </div>
    `).join('');
}

// ─────────────────────────────────────
// Filters
// ─────────────────────────────────────

function applyFilters() {
    const status = document.getElementById('filterStatus').value;
    const category = document.getElementById('filterCategory').value;

    let filtered = [...allMedicines];
    if (status !== 'all') filtered = filtered.filter(m => m.status === status);
    if (category !== 'all') filtered = filtered.filter(m => m.category === category);

    renderMedicineGrid(filtered);
}

// ─────────────────────────────────────
// Calendar
// ─────────────────────────────────────

async function loadCalendar() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/calendar`);
        const data = await res.json();
        if (data.success) {
            renderCalendar(data.calendar);
        }
    } catch (err) {
        document.getElementById('calendarStrip').innerHTML = '<p class="text-gray-500 text-sm">Could not load calendar.</p>';
    }
}

function renderCalendar(calendar) {
    const strip = document.getElementById('calendarStrip');

    if (!calendar.length) {
        strip.innerHTML = '<p class="text-gray-500 text-sm">No expiry data available yet.</p>';
        return;
    }

    strip.innerHTML = calendar.map(month => {
        const hasExpired = month.medicines.some(m => m.status === 'expired');
        const hasWarning = month.medicines.some(m => ['critical', 'warning'].includes(m.status));
        const cls = hasExpired ? 'has-expired' : hasWarning ? 'has-expiring' : '';

        const date = new Date(month.month + '-01');
        const monthName = date.toLocaleString('default', { month: 'short', year: 'numeric' });

        return `
            <div class="calendar-month ${cls}">
                <p class="font-bold text-sm">${monthName}</p>
                <p class="text-2xl font-display font-bold mt-1">${month.medicines.length}</p>
                <p class="text-xs text-gray-400">medicines</p>
            </div>
        `;
    }).join('');
}

// ─────────────────────────────────────
// AI Predictions
// ─────────────────────────────────────

async function loadPredictions() {
    try {
        const res = await fetch(`${API_BASE}/predictions`);
        const data = await res.json();
        if (data.success) {
            renderPredictions(data.predictions);
        }
    } catch (err) {
        document.getElementById('predictionsGrid').innerHTML = '<p class="text-gray-500 text-sm">Could not load predictions.</p>';
    }
}

function renderPredictions(predictions) {
    const grid = document.getElementById('predictionsGrid');

    if (!predictions.length) {
        grid.innerHTML = '<p class="text-gray-500 text-sm col-span-full">No predictions available yet. Log some consumption first.</p>';
        return;
    }

    grid.innerHTML = predictions.map(p => `
        <div class="bg-dark-800/30 rounded-2xl border border-purple-500/10 p-5 hover:border-purple-500/20 transition-colors">
            <div class="flex items-center gap-2 mb-3">
                <span class="text-lg">🤖</span>
                <h3 class="font-semibold text-sm">${p.medicine_name}</h3>
            </div>
            <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                    <span class="text-gray-400">Daily Usage</span>
                    <span class="font-medium">${p.daily_consumption_rate}/day</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Stock Lasts</span>
                    <span class="font-medium ${p.refill_urgent ? 'text-red-400' : 'text-green-400'}">${p.estimated_days_remaining} days</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-400">Refill By</span>
                    <span class="font-medium">${p.suggested_refill_date}</span>
                </div>
            </div>
            ${p.refill_urgent ? `<div class="mt-3 text-xs text-red-400 bg-red-500/10 rounded-lg px-3 py-2 font-medium">⚡ Refill urgently — running low!</div>` : ''}
            ${p.note ? `<div class="mt-3 text-xs text-gray-500">${p.note}</div>` : ''}
        </div>
    `).join('');
}

// ─────────────────────────────────────
// Actions
// ─────────────────────────────────────

async function logConsumption(id) {
    try {
        await fetch(`${API_BASE}/medicines/${id}/consume`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity: 1 })
        });
        showToast('Dose logged!', 'success');
        loadInventory();
    } catch (err) {
        showToast('Failed to log dose', 'error');
    }
}

async function removeMedicine(id) {
    if (!confirm('Remove this medicine?')) return;
    try {
        await fetch(`${API_BASE}/medicines/${id}`, { method: 'DELETE' });
        showToast('Medicine removed', 'success');
        loadInventory();
        loadCalendar();
    } catch (err) {
        showToast('Failed to remove', 'error');
    }
}

// ─────────────────────────────────────
// Utils
// ─────────────────────────────────────

function getGradient(status) {
    const g = { expired:'from-red-500 to-red-700', critical:'from-red-400 to-red-600', warning:'from-amber-400 to-amber-600', soon:'from-blue-400 to-blue-600', safe:'from-green-400 to-green-600' };
    return g[status] || 'from-gray-400 to-gray-600';
}

function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 400); }, 3000);
}
