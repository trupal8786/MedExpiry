/**
 * MedExpiry — Donate Page Logic
 * Handles: Leaflet Map, NGO listing, Donation actions
 */

const API_BASE = 'http://localhost:5000/api';
let map = null;
let markers = [];

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadNGOs();
    loadDonatableMedicines();
});

// ─────────────────────────────────────
// Map Initialization (Leaflet — FREE, no API key)
// ─────────────────────────────────────

function initMap() {
    // Center on India
    map = L.map('map', {
        center: [20.5937, 78.9629],
        zoom: 5,
        zoomControl: true,
        scrollWheelZoom: true,
    });

    // Dark theme tile layer (free)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap © CartoDB',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);

    document.getElementById('mapLoading').style.display = 'none';

    // Try to get user location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                map.setView([pos.coords.latitude, pos.coords.longitude], 11);
                L.circleMarker([pos.coords.latitude, pos.coords.longitude], {
                    radius: 8, fillColor: '#3b82f6', fillOpacity: 0.9,
                    color: '#fff', weight: 2
                }).addTo(map).bindPopup('📍 You are here');
            },
            () => {} // Silently fail
        );
    }
}

// ─────────────────────────────────────
// Load NGOs
// ─────────────────────────────────────

async function loadNGOs() {
    try {
        const res = await fetch(`${API_BASE}/ngos`);
        const data = await res.json();
        if (data.success) {
            renderNGOList(data.ngos);
            addMapMarkers(data.ngos);
        }
    } catch (err) {
        document.getElementById('ngoList').innerHTML =
            '<p class="p-4 text-gray-500 text-sm">Could not load NGO data. Start the backend.</p>';
    }
}

function renderNGOList(ngos) {
    const list = document.getElementById('ngoList');

    list.innerHTML = ngos.map(ngo => `
        <div class="ngo-card" onclick="focusNGO(${ngo.lat}, ${ngo.lng}, '${ngo.id}')">
            <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-xl bg-brand-500/10 flex items-center justify-center text-lg flex-shrink-0">
                    ${ngo.type === 'NGO' ? '🏥' : ngo.type === 'Government' ? '🏛️' : '📦'}
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                        <h3 class="font-semibold text-sm truncate">${ngo.name}</h3>
                        ${ngo.verified ? '<span class="text-xs text-brand-400">✓</span>' : ''}
                    </div>
                    <p class="text-xs text-gray-400 mt-0.5">${ngo.city} • ${ngo.type}</p>
                    <p class="text-xs text-gray-500 mt-1 line-clamp-2">${ngo.address}</p>
                    <div class="flex items-center gap-3 mt-2">
                        <span class="text-xs text-gray-400">⏰ ${ngo.timing}</span>
                    </div>
                    <div class="flex flex-wrap gap-1 mt-2">
                        ${ngo.accepts.slice(0, 3).map(a => `<span class="text-[10px] bg-white/5 px-2 py-0.5 rounded-full text-gray-400">${a}</span>`).join('')}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function addMapMarkers(ngos) {
    ngos.forEach(ngo => {
        const icon = L.divIcon({
            html: `<div style="background:#22c55e; border:3px solid white; border-radius:50%; width:16px; height:16px; box-shadow: 0 0 10px rgba(34,197,94,0.5);"></div>`,
            className: '',
            iconSize: [16, 16],
            iconAnchor: [8, 8]
        });

        const marker = L.marker([ngo.lat, ngo.lng], { icon })
            .addTo(map)
            .bindPopup(`
                <div style="min-width:200px; color:#222;">
                    <strong>${ngo.name}</strong><br>
                    <small>${ngo.type} • ${ngo.city}</small><br>
                    <small>${ngo.address}</small><br>
                    <small>📞 ${ngo.phone}</small><br>
                    <small>⏰ ${ngo.timing}</small>
                </div>
            `);

        markers.push({ id: ngo.id, marker });
    });
}

function focusNGO(lat, lng, id) {
    map.setView([lat, lng], 14, { animate: true });

    // Highlight card
    document.querySelectorAll('.ngo-card').forEach(c => c.classList.remove('active'));
    event.currentTarget.classList.add('active');

    // Open popup
    const found = markers.find(m => m.id === id);
    if (found) found.marker.openPopup();
}

// ─────────────────────────────────────
// Donatable Medicines
// ─────────────────────────────────────

async function loadDonatableMedicines() {
    try {
        const res = await fetch(`${API_BASE}/donate/eligible`);
        const data = await res.json();
        if (data.success) {
            renderDonatableMeds(data.medicines);
        }
    } catch (err) {
        document.getElementById('donatableMeds').innerHTML =
            '<p class="text-gray-500">Could not load medicines.</p>';
    }
}

function renderDonatableMeds(medicines) {
    const container = document.getElementById('donatableMeds');

    if (!medicines.length) {
        container.innerHTML = '<p class="text-gray-500">No medicines eligible for donation right now.</p>';
        return;
    }

    container.innerHTML = medicines.map(med => `
        <div class="flex items-center justify-between bg-dark-800/50 rounded-xl px-3 py-2.5 border border-white/5">
            <div class="flex items-center gap-2">
                <span class="w-7 h-7 rounded-lg bg-brand-500/10 flex items-center justify-center text-xs font-bold text-brand-400">${med.name.charAt(0)}</span>
                <div>
                    <p class="font-medium text-xs">${med.name}</p>
                    <p class="text-[10px] text-gray-500">${med.days_until_expiry} days left • Qty: ${med.quantity}</p>
                </div>
            </div>
            <button onclick="donateMedicine('${med.id}')" class="text-[10px] bg-pink-500/10 text-pink-400 hover:bg-pink-500/20 px-2.5 py-1 rounded-lg font-medium transition-colors">
                Donate
            </button>
        </div>
    `).join('');
}

async function donateMedicine(medId) {
    // Use the first NGO as default for demo
    const ngoId = 'ngo_001';
    try {
        const res = await fetch(`${API_BASE}/donate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ medicine_id: medId, ngo_id: ngoId })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            loadDonatableMedicines();
        } else {
            showToast(data.error || 'Donation failed', 'error');
        }
    } catch (err) {
        showToast('Server error', 'error');
    }
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
