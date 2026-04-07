/**
 * MedExpiry — Scanner Logic
 * Handles: Webcam, File Upload, OCR API calls, Results display
 */

const API_BASE = 'http://localhost:5000/api';

let stream = null;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('startCameraBtn').addEventListener('click', startCamera);
    document.getElementById('captureBtn').addEventListener('click', captureAndScan);
    document.getElementById('closeCameraBtn').addEventListener('click', closeCamera);
    document.getElementById('fileInput').addEventListener('change', handleFileUpload);
    document.getElementById('demoScanBtn').addEventListener('click', runDemoScan);
});

// ─────────────────────────────────────
// Camera Controls
// ─────────────────────────────────────

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } }
        });
        const video = document.getElementById('cameraPreview');
        video.srcObject = stream;
        video.classList.remove('hidden');
        document.getElementById('scanDefault').classList.add('hidden');
        document.getElementById('cameraControls').classList.remove('hidden');
        document.getElementById('imagePreview').classList.add('hidden');
    } catch (err) {
        alert('Camera access denied. Please allow camera permission or upload a photo instead.');
        console.error('Camera error:', err);
    }
}

function closeCamera() {
    if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
    }
    document.getElementById('cameraPreview').classList.add('hidden');
    document.getElementById('cameraControls').classList.add('hidden');
    document.getElementById('scanDefault').classList.remove('hidden');
}

async function captureAndScan() {
    const video = document.getElementById('cameraPreview');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    closeCamera();

    // Show captured image
    const imgPreview = document.getElementById('imagePreview');
    imgPreview.src = canvas.toDataURL('image/jpeg');
    imgPreview.classList.remove('hidden');

    // Convert to blob and send
    canvas.toBlob(blob => {
        sendImageToOCR(blob, 'capture.jpg');
    }, 'image/jpeg', 0.9);
}

// ─────────────────────────────────────
// File Upload
// ─────────────────────────────────────

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        const imgPreview = document.getElementById('imagePreview');
        imgPreview.src = e.target.result;
        imgPreview.classList.remove('hidden');
        document.getElementById('scanDefault').classList.add('hidden');
    };
    reader.readAsDataURL(file);

    sendImageToOCR(file, file.name);
}

// ─────────────────────────────────────
// OCR API Call
// ─────────────────────────────────────

async function sendImageToOCR(blob, filename) {
    showScanOverlay(true);

    const formData = new FormData();
    formData.append('image', blob, filename);

    try {
        const res = await fetch(`${API_BASE}/scan`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        showScanOverlay(false);

        if (data.success) {
            renderScanResults(data);
        } else {
            renderScanError(data.error || 'Scan failed');
        }
    } catch (err) {
        showScanOverlay(false);
        renderScanError('Server not reachable. Is the backend running?');
    }
}

// ─────────────────────────────────────
// Demo Scan
// ─────────────────────────────────────

async function runDemoScan() {
    showScanOverlay(true);
    document.getElementById('scanDefault').classList.add('hidden');

    try {
        const res = await fetch(`${API_BASE}/scan/demo`);
        const data = await res.json();

        showScanOverlay(false);
        renderScanResults(data);
    } catch (err) {
        showScanOverlay(false);
        renderScanError('Server not reachable. Start the backend first.');
    }
}

// ─────────────────────────────────────
// UI Updates
// ─────────────────────────────────────

function showScanOverlay(show) {
    document.getElementById('scanOverlay').classList.toggle('hidden', !show);
}

function renderScanResults(data) {
    const container = document.getElementById('resultsContent');
    const defaultEl = document.getElementById('resultsDefault');
    const ext = data.extracted_data;

    defaultEl.classList.add('hidden');
    container.classList.remove('hidden');

    const statusColors = {
        expired: 'text-red-400 bg-red-500/10',
        critical: 'text-red-400 bg-red-500/10',
        warning: 'text-amber-400 bg-amber-500/10',
        soon: 'text-blue-400 bg-blue-500/10',
        safe: 'text-green-400 bg-green-500/10',
    };

    const color = statusColors[ext.status] || 'text-gray-400 bg-gray-500/10';

    container.innerHTML = `
        <div class="space-y-6">
            <!-- Confidence -->
            <div>
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs text-gray-400 font-medium">OCR CONFIDENCE</span>
                    <span class="text-xs font-bold ${data.confidence >= 0.7 ? 'text-green-400' : data.confidence >= 0.4 ? 'text-amber-400' : 'text-red-400'}">${(data.confidence * 100).toFixed(0)}%</span>
                </div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${data.confidence * 100}%"></div>
                </div>
            </div>

            <!-- Medicine Name -->
            <div class="bg-dark-800/50 rounded-2xl p-5 border border-white/5">
                <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">Medicine Name</p>
                <p class="text-2xl font-display font-bold">${ext.medicine_name}</p>
            </div>

            <!-- Expiry Status -->
            <div class="bg-dark-800/50 rounded-2xl p-5 border border-white/5">
                <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">Expiry Date</p>
                <p class="text-xl font-bold">${ext.expiry_display}</p>
                <div class="mt-2 inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-semibold ${color}">
                    ${ext.status === 'safe' ? '✅ Safe' : ext.status === 'expired' ? '🚫 Expired' : ext.status === 'critical' ? '🔴 Expires Very Soon' : ext.status === 'warning' ? '🟡 Expiring Soon' : '🔵 Expiring'}
                    ${ext.days_until_expiry != null ? ` — ${ext.days_until_expiry > 0 ? ext.days_until_expiry + ' days left' : Math.abs(ext.days_until_expiry) + ' days ago'}` : ''}
                </div>
            </div>

            <!-- Details Grid -->
            <div class="grid grid-cols-2 gap-3">
                ${ext.batch_number ? `
                <div class="bg-dark-800/50 rounded-xl p-3 border border-white/5">
                    <p class="text-xs text-gray-500">Batch No.</p>
                    <p class="font-semibold text-sm mt-1">${ext.batch_number}</p>
                </div>` : ''}
                ${ext.mfg_date ? `
                <div class="bg-dark-800/50 rounded-xl p-3 border border-white/5">
                    <p class="text-xs text-gray-500">Mfg. Date</p>
                    <p class="font-semibold text-sm mt-1">${ext.mfg_date}</p>
                </div>` : ''}
                ${ext.mrp ? `
                <div class="bg-dark-800/50 rounded-xl p-3 border border-white/5">
                    <p class="text-xs text-gray-500">MRP</p>
                    <p class="font-semibold text-sm mt-1">${ext.mrp}</p>
                </div>` : ''}
            </div>

            <!-- Add to Inventory Button -->
            <button onclick="addToInventory(${JSON.stringify(ext).replace(/"/g, '&quot;')})" class="w-full py-3.5 bg-brand-500 hover:bg-brand-600 text-white font-semibold rounded-2xl transition-all shadow-lg shadow-brand-500/25 hover:shadow-brand-500/40 flex items-center justify-center gap-2">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
                Add to Inventory
            </button>
        </div>
    `;
}

function renderScanError(message) {
    const container = document.getElementById('resultsContent');
    const defaultEl = document.getElementById('resultsDefault');

    defaultEl.classList.add('hidden');
    container.classList.remove('hidden');

    container.innerHTML = `
        <div class="text-center py-8">
            <div class="text-5xl mb-4">❌</div>
            <p class="text-red-400 font-semibold mb-2">Scan Failed</p>
            <p class="text-gray-400 text-sm">${message}</p>
            <button onclick="location.reload()" class="mt-4 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-sm font-medium transition-colors">Try Again</button>
        </div>
    `;
}

// ─────────────────────────────────────
// Add to Inventory
// ─────────────────────────────────────

async function addToInventory(extractedData) {
    try {
        const res = await fetch(`${API_BASE}/medicines`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(extractedData)
        });
        const data = await res.json();

        if (data.success) {
            showToast(`${data.medicine.name} added to inventory!`, 'success');
        } else {
            showToast('Failed to add medicine', 'error');
        }
    } catch (err) {
        showToast('Server error. Is the backend running?', 'error');
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
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}
