/* ============================================================
   Health Wallet — Main Application JavaScript
   SPA router, API client, and all view controllers
   ============================================================ */

const API = '';  // Same origin

// ============================================================
// NAVIGATION
// ============================================================

function navigate(view) {
    // Update URL hash
    window.location.hash = view;

    // Hide all views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

    // Show target view
    const target = document.getElementById(`view-${view}`);
    if (target) target.classList.add('active');

    // Update nav
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const navItem = document.querySelector(`.nav-item[data-view="${view}"]`);
    if (navItem) navItem.classList.add('active');

    // Close mobile nav
    document.querySelector('.sidebar')?.classList.remove('open');

    // Load view data
    if (view === 'dashboard') loadDashboard();
    else if (view === 'vault') loadVault();
}

// Hash-based routing
window.addEventListener('hashchange', () => {
    const hash = window.location.hash.slice(1) || 'dashboard';
    navigate(hash);
});

// ============================================================
// HEALTH CHECK
// ============================================================

async function checkSystemHealth() {
    try {
        const resp = await fetch(`${API}/api/health`);
        const data = await resp.json();

        // Ollama status
        const ollamaStatus = data.components?.ollama?.status || 'unknown';
        const ollamaDot = document.getElementById('ollama-dot');
        const ollamaText = document.getElementById('ollama-status');

        if (ollamaStatus === 'healthy') {
            ollamaDot.className = 'status-dot green';
            ollamaText.textContent = data.components.ollama.model || 'Connected';
        } else if (ollamaStatus === 'offline') {
            ollamaDot.className = 'status-dot red';
            ollamaText.textContent = 'Offline';
        } else {
            ollamaDot.className = 'status-dot yellow';
            ollamaText.textContent = ollamaStatus;
        }

        // MongoDB status
        const mongoStatus = data.components?.mongodb?.status || 'unknown';
        const mongoDot = document.getElementById('mongo-dot');
        const mongoText = document.getElementById('mongo-status');

        if (mongoStatus === 'connected') {
            mongoDot.className = 'status-dot green';
            mongoText.textContent = 'Connected';
        } else if (mongoStatus === 'not_configured') {
            mongoDot.className = 'status-dot yellow';
            mongoText.textContent = 'Fallback';
        } else {
            mongoDot.className = 'status-dot red';
            mongoText.textContent = 'Error';
        }

        return data;
    } catch (e) {
        console.error('Health check failed:', e);
        document.getElementById('ollama-dot').className = 'status-dot red';
        document.getElementById('ollama-status').textContent = 'API Error';
        return null;
    }
}

// ============================================================
// DASHBOARD
// ============================================================

async function loadDashboard() {
    try {
        // Load records count
        const vaultResp = await fetch(`${API}/api/vault/records`);
        const vaultData = await vaultResp.json();
        const records = vaultData.records || [];
        document.getElementById('stat-records').textContent = vaultData.count || 0;
        document.getElementById('vault-count').textContent = vaultData.count || 0;

        // Count prescriptions
        const prescriptionCount = records.filter(r =>
            r.title?.toLowerCase().includes('prescription') ||
            r.category === 'medications'
        ).length;
        document.getElementById('stat-prescriptions').textContent = prescriptionCount;

        // Load metrics for consultation count
        try {
            const metricsResp = await fetch(`${API}/api/health/metrics`);
            const metrics = await metricsResp.json();
            document.getElementById('stat-consultations').textContent = metrics.total_requests || 0;
        } catch (e) {
            document.getElementById('stat-consultations').textContent = '0';
        }

        // Routing count — from care router usage
        document.getElementById('stat-routing').textContent = sessionRoutingCount || 0;

    } catch (e) {
        console.error('Dashboard load failed:', e);
    }
}

// Track routing count in session
let sessionRoutingCount = 0;

// ============================================================
// HEALTH RECORDS
// ============================================================

let allRecords = [];

async function loadVault() {
    try {
        const resp = await fetch(`${API}/api/vault/records`);
        const data = await resp.json();
        allRecords = data.records || [];
        renderRecords(allRecords);
    } catch (e) {
        console.error('Records load failed:', e);
    }
}

function renderRecords(records) {
    const grid = document.getElementById('records-grid');

    const iconMap = {
        medications: '💊',
        timeline: '📅',
        general: '📄',
    };

    const colorMap = {
        medications: 'purple',
        timeline: 'pink',
        general: 'teal',
    };

    grid.innerHTML = records.map(r => `
        <div class="record-card" onclick="openRecord('${r.id}')">
            <div class="record-icon stat-icon ${colorMap[r.category] || 'teal'}">
                ${iconMap[r.category] || '📄'}
            </div>
            <div class="record-title">${escapeHtml(r.title)}</div>
            <div class="record-category">${r.category.replace('_', ' ')}</div>
            <div class="record-preview">${escapeHtml(r.preview)}</div>
            <div class="record-date">Modified: ${new Date(r.modified).toLocaleDateString()}</div>
        </div>
    `).join('');
}

function filterVault(category, btn) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');

    if (category === 'all') {
        renderRecords(allRecords);
    } else {
        renderRecords(allRecords.filter(r => r.category === category));
    }
}

function searchVault(query) {
    if (!query.trim()) {
        renderRecords(allRecords);
        return;
    }
    const q = query.toLowerCase();
    renderRecords(allRecords.filter(r =>
        r.title.toLowerCase().includes(q) ||
        r.preview.toLowerCase().includes(q) ||
        r.category.toLowerCase().includes(q)
    ));
}

async function openRecord(id) {
    try {
        const resp = await fetch(`${API}/api/vault/records/${id}`);
        const record = await resp.json();

        document.getElementById('record-detail').innerHTML = renderMarkdown(record.content);
        document.getElementById('record-modal').classList.remove('hidden');
    } catch (e) {
        console.error('Failed to open record:', e);
    }
}

function closeModal() {
    document.getElementById('record-modal').classList.add('hidden');
}

// ============================================================
// AI CHAT
// ============================================================

let isChatBusy = false;
let currentModelName = 'DeepSeek R1';

async function sendChat() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message || isChatBusy) return;

    isChatBusy = true;
    input.value = '';
    document.getElementById('btn-send').disabled = true;

    // Add user message
    addChatMessage('user', message);

    // Add typing indicator
    const typingId = addTypingIndicator();

    try {
        // SSE streaming
        const resp = await fetch(`${API}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, stream: true }),
        });

        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Create assistant message bubble
        const msgEl = addChatMessage('assistant', '', true);
        const contentEl = msgEl.querySelector('.msg-content');

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.token) {
                            fullResponse += data.token;
                            contentEl.innerHTML = renderMarkdown(fullResponse);
                            scrollChatToBottom();
                        }
                        if (data.error) {
                            contentEl.innerHTML = `<span style="color:var(--accent-red);">Error: ${escapeHtml(data.error)}</span>`;
                        }
                    } catch (e) { }
                }
            }
        }

        if (!fullResponse) {
            contentEl.innerHTML = '<span style="color:var(--text-muted);">No response received. Is Ollama running?</span>';
        }

    } catch (e) {
        removeTypingIndicator(typingId);
        addChatMessage('assistant', `Error: Could not reach the AI model. Make sure Ollama is running.\n\n\`${e.message}\``);
    }

    isChatBusy = false;
    document.getElementById('btn-send').disabled = false;
    input.focus();
}

function addChatMessage(role, content, empty = false) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `chat-message ${role}`;

    if (role === 'assistant') {
        div.innerHTML = `<div class="model-tag">🤖 ${escapeHtml(currentModelName)} — Health Assistant</div><div class="msg-content">${empty ? '<span class="animate-pulse" style="color:var(--text-muted)">Thinking...</span>' : renderMarkdown(content)}</div>`;
    } else {
        div.textContent = content;
    }

    container.appendChild(div);
    scrollChatToBottom();
    return div;
}

function addTypingIndicator() {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = 'typing-' + Date.now();
    div.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(div);
    scrollChatToBottom();
    return div.id;
}

function removeTypingIndicator(id) {
    document.getElementById(id)?.remove();
}

function scrollChatToBottom() {
    const container = document.getElementById('chat-messages');
    container.scrollTop = container.scrollHeight;
}

// ============================================================
// CARE ROUTER
// ============================================================

async function routePatient() {
    const input = document.getElementById('care-input').value.trim();
    if (!input) return;

    const btn = document.getElementById('btn-route');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;"></span> Processing...';

    // Animate bridge steps
    animateBridge(1);

    try {
        // Step 1: Anonymize
        animateBridge(2);
        const anonResp = await fetch(`${API}/api/care/anonymize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_data: input }),
        });
        const anonData = await anonResp.json();
        document.getElementById('anonymized-output').innerHTML = `
            <div style="color:var(--accent-green);font-weight:600;margin-bottom:8px;">✅ PII Stripped Successfully</div>
            <div>${escapeHtml(anonData.anonymized)}</div>
            <div style="margin-top:8px;font-size:12px;color:var(--text-muted);">
                Original: ${anonData.original_length} chars → Anonymized: ${anonData.anonymized_length} chars
            </div>
        `;

        // Step 2-4: Route
        animateBridge(3);
        const routeResp = await fetch(`${API}/api/care/route`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                clinical_intent: anonData.anonymized,
                city: 'San Francisco',
            }),
        });
        const routeData = await routeResp.json();

        animateBridge(4);
        await sleep(500);
        animateBridge(5);

        // Track routing count
        sessionRoutingCount++;

        // Display results
        displayRouteResults(routeData);

    } catch (e) {
        console.error('Routing failed:', e);
        document.getElementById('anonymized-output').innerHTML =
            `<span style="color:var(--accent-red);">Error: ${escapeHtml(e.message)}. Is the backend running?</span>`;
    }

    btn.disabled = false;
    btn.innerHTML = '🩺 Route to Specialist';
}

function displayRouteResults(data) {
    const resultsDiv = document.getElementById('care-results');
    resultsDiv.classList.remove('hidden');

    // Specialty
    document.getElementById('care-specialty').innerHTML = `
        <div class="card" style="border-left:3px solid var(--accent-primary);">
            <div style="font-size:14px;color:var(--accent-primary);font-weight:600;">Recommended Specialty</div>
            <div style="font-size:22px;font-weight:800;margin:4px 0;">${escapeHtml(data.specialty?.charAt(0).toUpperCase() + data.specialty?.slice(1))}</div>
            <div style="font-size:13px;color:var(--text-secondary);">${escapeHtml(data.reasoning || '')}</div>
            <div style="font-size:12px;color:var(--accent-green);margin-top:8px;">🔒 ${escapeHtml(data.privacy_note || '')}</div>
        </div>
    `;

    // Providers
    const providers = data.providers || [];
    document.getElementById('care-providers').innerHTML = providers.map(p => `
        <div class="provider-card">
            <div class="provider-name">${escapeHtml(p.name)}</div>
            <div class="provider-specialty">${escapeHtml(p.specialty)}</div>
            <div class="provider-hospital">🏥 ${escapeHtml(p.hospital)} · ${escapeHtml(p.city)}</div>
            <div class="provider-rating">${'⭐'.repeat(Math.round(p.rating || 0))} ${p.rating || '—'}</div>
            <span class="provider-status ${p.accepting_new ? 'accepting' : 'full'}">
                ${p.accepting_new ? '✓ Accepting Patients' : '✕ Not Accepting'}
            </span>
            ${p.conditions ? `<div style="margin-top:8px;font-size:12px;color:var(--text-muted);">Specializes in: ${p.conditions.join(', ')}</div>` : ''}
        </div>
    `).join('');

    // Drug interactions
    if (data.drug_interactions && data.drug_interactions.length > 0) {
        document.getElementById('care-drugs').innerHTML = `
            <h3 style="font-size:16px;font-weight:700;margin-bottom:12px;">⚠️ Drug Interaction Alerts</h3>
            ${data.drug_interactions.map(d => `
                <div class="drug-alert ${d.severity}">
                    <div class="alert-icon">${d.severity === 'critical' ? '🚨' : d.severity === 'high' ? '⚠️' : '⚡'}</div>
                    <div>
                        <div class="alert-title">${escapeHtml(d.drug_a)} + ${escapeHtml(d.drug_b)} (${d.severity.toUpperCase()})</div>
                        <div class="alert-desc">${escapeHtml(d.description)}</div>
                        <div style="font-size:12px;color:var(--accent-primary);margin-top:4px;">💡 ${escapeHtml(d.recommendation)}</div>
                    </div>
                </div>
            `).join('')}
        `;
    } else {
        document.getElementById('care-drugs').innerHTML = '';
    }
}

async function checkDrugs() {
    const medications = ['escitalopram', 'ibuprofen'];
    try {
        const resp = await fetch(`${API}/api/care/drug-check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ medications }),
        });
        const data = await resp.json();

        const resultsDiv = document.getElementById('care-results');
        resultsDiv.classList.remove('hidden');
        document.getElementById('care-drugs').innerHTML = `
            <h3 style="font-size:16px;font-weight:700;margin-bottom:12px;">💊 Drug Interaction Check: ${medications.join(' + ')}</h3>
            ${data.interactions.length === 0 ? '<div style="color:var(--accent-green);">✅ No known interactions found.</div>' :
                data.interactions.map(d => `
                    <div class="drug-alert ${d.severity}">
                        <div class="alert-icon">${d.severity === 'critical' ? '🚨' : d.severity === 'high' ? '⚠️' : '⚡'}</div>
                        <div>
                            <div class="alert-title">${escapeHtml(d.drug_a)} + ${escapeHtml(d.drug_b)} (${d.severity.toUpperCase()})</div>
                            <div class="alert-desc">${escapeHtml(d.description)}</div>
                            <div style="font-size:12px;color:var(--accent-primary);margin-top:4px;">💡 ${escapeHtml(d.recommendation)}</div>
                        </div>
                    </div>
                `).join('')
            }
        `;
    } catch (e) {
        console.error('Drug check failed:', e);
    }
}

function animateBridge(step) {
    for (let i = 1; i <= 5; i++) {
        const node = document.getElementById(`bridge-step-${i}`);
        node.classList.toggle('active', i <= step);
    }
}

// ============================================================
// UTILITIES
// ============================================================

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function renderMarkdown(text) {
    if (!text) return '';

    // Handle DeepSeek R1 <think>...</think> reasoning blocks
    // Show as collapsible "Reasoning" section
    text = text.replace(/<think>([\s\S]*?)<\/think>/g, (match, thinking) => {
        const trimmed = thinking.trim();
        if (!trimmed) return '';
        return `<details class="think-block"><summary>💭 Reasoning (click to expand)</summary><div class="think-content">${trimmed}</div></details>`;
    });

    // Remove incomplete <think> blocks (still streaming)
    text = text.replace(/<think>[\s\S]*$/, '<span class="thinking-indicator">💭 Reasoning...</span>');

    return text
        // Headers
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        // Bold and italic
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Tables
        .replace(/\|(.+)\|/g, (match) => {
            const cells = match.split('|').filter(c => c.trim());
            if (cells.every(c => /^[-:]+$/.test(c.trim()))) return '';
            const tag = cells.some(c => /^[-:]+$/.test(c.trim())) ? 'td' : 'td';
            return '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
        })
        // Lists
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
        // Line breaks
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>');
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================
// MODEL SWITCHING
// ============================================================

let _availableModels = [];

async function refreshModelList() {
    try {
        const resp = await fetch(`${API}/api/health/models`);
        const data = await resp.json();
        const select = document.getElementById('model-select');
        if (!select) return;

        const currentModel = data.current_model || '';
        const models = data.available_models || [];
        _availableModels = models;

        // Build options — put current model first
        const modelNames = models.map(m => m.name || m.model || '');

        // Deduplicate
        const uniqueModels = [...new Set(modelNames)].filter(Boolean);

        if (uniqueModels.length === 0) {
            select.innerHTML = `<option value="${escapeHtml(currentModel)}">${escapeHtml(formatModelName(currentModel))}</option>`;
        } else {
            select.innerHTML = uniqueModels.map(name => {
                const selected = name === currentModel ? 'selected' : '';
                return `<option value="${escapeHtml(name)}" ${selected}>${escapeHtml(formatModelName(name))}</option>`;
            }).join('');
        }

        // Update current model display name
        currentModelName = formatModelName(currentModel);
        const tag = document.getElementById('chat-model-tag');
        if (tag) tag.textContent = `🤖 ${currentModelName} — Health Assistant`;

    } catch (e) {
        console.error('Failed to load models:', e);
    }
}

function formatModelName(modelStr) {
    if (!modelStr) return 'Unknown';
    // "deepseek-r1:7b" → "DeepSeek R1 7B"
    return modelStr
        .replace(/:/g, ' ')
        .replace(/-/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

async function switchModel(modelName) {
    if (!modelName) return;
    try {
        // Update the backend model
        const resp = await fetch(`${API}/api/health/switch-model`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: modelName }),
        });
        const data = await resp.json();

        if (data.status === 'ok') {
            currentModelName = formatModelName(modelName);
            const tag = document.getElementById('chat-model-tag');
            if (tag) tag.textContent = `🤖 ${currentModelName} — Health Assistant`;

            // Add a system message in chat
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'chat-message assistant';
            div.innerHTML = `<div class="model-tag">⚙️ System</div><div class="msg-content" style="font-style:italic;color:var(--text-secondary);">Model switched to <strong>${escapeHtml(currentModelName)}</strong>. Conversation history has been preserved.</div>`;
            container.appendChild(div);
            scrollChatToBottom();
        }
    } catch (e) {
        console.error('Failed to switch model:', e);
        alert('Failed to switch model. Is the backend running?');
    }
}

// ============================================================
// PRESCRIPTION SCANNER
// ============================================================

function initPrescriptionScanner() {
    const dropzone = document.getElementById('scanner-dropzone');
    const fileInput = document.getElementById('scanner-file-input');
    const content = document.getElementById('dropzone-content');
    const processing = document.getElementById('scanner-processing');
    const statusText = document.getElementById('processing-status');

    if (!dropzone || !fileInput) return;

    // Trigger file input on click
    dropzone.addEventListener('click', (e) => {
        if (!processing.classList.contains('hidden')) return;
        fileInput.click();
    });

    // Drag and drop events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (processing.classList.contains('hidden')) {
                dropzone.classList.add('dragover');
            }
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length && processing.classList.contains('hidden')) {
            handlePrescriptionUpload(files[0]);
        }
    }, false);

    fileInput.addEventListener('change', (e) => {
        if (fileInput.files.length && processing.classList.contains('hidden')) {
            handlePrescriptionUpload(fileInput.files[0]);
        }
    });

    async function handlePrescriptionUpload(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file (PNG, JPG, WEBP).');
            return;
        }

        // Show processing state
        content.classList.add('hidden');
        processing.classList.remove('hidden');
        statusText.textContent = 'Reading prescription text...';

        // Dynamic status updates for premium experience
        const statusInterval = setTimeout(() => {
            statusText.textContent = 'Structuring prescription...';
        }, 3000);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const resp = await fetch(`${API}/api/vault/upload-prescription`, {
                method: 'POST',
                body: formData
            });

            if (!resp.ok) {
                const errData = await resp.json();
                throw new Error(errData.detail || 'Failed to process prescription');
            }

            const data = await resp.json();
            
            // Success! Clear timer, refresh vault and open the new record
            clearTimeout(statusInterval);
            await loadVault();
            if (data.record && data.record.id) {
                openRecord(data.record.id);
            }

        } catch (e) {
            clearTimeout(statusInterval);
            console.error('Prescription processing failed:', e);
            alert(`Error: ${e.message}`);
        } finally {
            // Restore dropzone state
            fileInput.value = '';
            processing.classList.add('hidden');
            content.classList.remove('hidden');
        }
    }
}

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    const hash = window.location.hash.slice(1) || 'dashboard';
    navigate(hash);
    checkSystemHealth();
    initPrescriptionScanner();
    refreshModelList();

    // Auto-resize chat textarea
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
        });
    }
});

