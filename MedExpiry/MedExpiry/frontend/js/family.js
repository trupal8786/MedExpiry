/**
 * MedExpiry — Family Sharing Logic
 */

const API_BASE = '/api'; // Updated for live deployment!

async function createFamily() {
    const name = document.getElementById('familyName').value.trim();
    const creator = document.getElementById('creatorName').value.trim();
    
    if (!name || !creator) {
        showResult('createResult', 'Please fill in all fields.', 'error');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/family`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, creator })
        });
        const data = await res.json();

        if (data.success) {
            showResult('createResult', `
                <div class="bg-brand-500/10 border border-brand-500/20 rounded-xl p-4">
                    <p class="text-brand-400 font-semibold mb-2">✅ Family Created!</p>
                    <p class="text-sm text-gray-300">Share this invite code with your family:</p>
                    <div class="mt-2 bg-dark-900 rounded-lg px-4 py-3 text-center">
                        <span class="text-3xl font-display font-bold tracking-[0.3em] text-white">${data.family.invite_code}</span>
                    </div>
                    <p class="text-xs text-gray-500 mt-2">Members: ${data.family.members.join(', ')}</p>
                </div>
            `, 'html');
        } else {
            showResult('createResult', data.error || 'Failed to create family.', 'error');
        }
    } catch (err) {
        showResult('createResult', 'Server not reachable.', 'error');
    }
}

async function joinFamily() {
    const code = document.getElementById('inviteCode').value.trim().toUpperCase();
    const member = document.getElementById('memberName').value.trim();
    
    if (!code || !member) {
        showResult('joinResult', 'Please fill in all fields.', 'error');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/family/join`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ invite_code: code, member })
        });
        const data = await res.json();

        if (data.success) {
            showResult('joinResult', `
                <div class="bg-brand-500/10 border border-brand-500/20 rounded-xl p-4">
                    <p class="text-brand-400 font-semibold mb-1">✅ Joined "${data.family.name}"!</p>
                    <p class="text-xs text-gray-400">Members: ${data.family.members.join(', ')}</p>
                </div>
            `, 'html');
        } else {
            showResult('joinResult', data.error || 'Invalid invite code.', 'error');
        }
    } catch (err) {
        showResult('joinResult', 'Server not reachable.', 'error');
    }
}

function showResult(elementId, content, type = 'success') {
    const el = document.getElementById(elementId);
    el.classList.remove('hidden');
    
    if (type === 'html') {
        el.innerHTML = content;
    } else if (type === 'error') {
        el.innerHTML = `<div class="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-red-400 text-sm">${content}</div>`;
    } else {
        el.innerHTML = `<div class="bg-brand-500/10 border border-brand-500/20 rounded-xl p-3 text-brand-400 text-sm">${content}</div>`;
    }
}