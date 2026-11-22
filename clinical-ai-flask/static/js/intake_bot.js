// ============================================================
// CONVERSATIONAL INTAKE & RECEPTIONIST BOT FRONTEND
// Clinical AI Suite - Group 1 (Tanzeef Ahamed)
// ============================================================

const chatFeed = document.getElementById('chat-feed');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const quickRepliesEl = document.getElementById('quick-replies');
const resetBtn = document.getElementById('reset-chat-btn');
const intakeProgress = document.getElementById('intake-progress');
const progressCount = document.getElementById('progress-count');
const progressSteps = document.getElementById('progress-steps');
const modeTabs = document.querySelectorAll('.mode-tab');
const demoChips = document.querySelectorAll('.demo-chip');

const summaryStatus = document.getElementById('summary-status');
const sumFields = {
    patient_name: document.getElementById('sum-patient-name'),
    chief_complaint: document.getElementById('sum-chief-complaint'),
    duration_severity: document.getElementById('sum-duration-severity'),
    associated_symptoms: document.getElementById('sum-associated-symptoms'),
    medical_history: document.getElementById('sum-medical-history'),
};

const receiptCard = document.getElementById('receipt-card');
const receiptCode = document.getElementById('receipt-code');
const receiptDetails = document.getElementById('receipt-details');
const quickBookForm = document.getElementById('quick-book-form');
const qbPatient = document.getElementById('qb-patient');
const qbClinician = document.getElementById('qb-clinician');
const qbDatetime = document.getElementById('qb-datetime');
const qbReason = document.getElementById('qb-reason');
const qbFeedback = document.getElementById('qb-feedback');
const slotPills = document.getElementById('slot-pills');

const INTAKE_ORDER = [
    'patient_name',
    'chief_complaint',
    'duration_severity',
    'associated_symptoms',
    'medical_history',
];

let currentMode = 'intake';

function esc(str) {
    const div = document.createElement('div');
    div.textContent = str ?? '';
    return div.innerHTML;
}

function tagClass(tag) {
    if (!tag) return '';
    const lower = tag.toLowerCase();
    if (lower.includes('guardrail') || lower.includes('conflict')) return 'danger';
    if (lower.includes('validation')) return 'warn';
    if (lower.includes('complete') || lower.includes('confirm')) return 'success';
    return '';
}

function renderMessages(messages) {
    chatFeed.innerHTML = (messages || []).map((m) => {
        const isPatient = m.sender === 'patient';
        const avatar = isPatient ? 'YOU' : '+';
        const tagHtml = (!isPatient && m.tag)
            ? `<span class="msg-tag ${tagClass(m.tag)}">${esc(m.tag)}</span>`
            : '';
        return `
            <div class="chat-msg ${isPatient ? 'patient' : 'bot'}">
                <div class="msg-avatar">${avatar}</div>
                <div class="msg-bubble">
                    <div class="msg-meta">
                        ${tagHtml}
                        <span class="msg-time">${esc(m.timestamp || '')}</span>
                    </div>
                    <div class="msg-text">${esc(m.text)}</div>
                </div>
            </div>
        `;
    }).join('');
    chatFeed.scrollTop = chatFeed.scrollHeight;
}

function renderSummary(summary) {
    if (!summary) return;
    Object.entries(sumFields).forEach(([key, el]) => {
        const val = summary[key] || 'Pending';
        el.textContent = val;
        el.classList.toggle('pending', val === 'Pending');
    });

    if (summary.is_complete) {
        summaryStatus.textContent = 'Ready for Clinician Review';
        summaryStatus.classList.remove('in-progress');
        summaryStatus.classList.add('complete');
    } else {
        summaryStatus.textContent = 'In Progress';
        summaryStatus.classList.remove('complete');
        summaryStatus.classList.add('in-progress');
    }

    if (summary.patient_name !== 'Pending' && !qbPatient.value) {
        qbPatient.value = summary.patient_name;
    }
    if (summary.chief_complaint !== 'Pending' && !qbReason.value) {
        qbReason.value = summary.chief_complaint;
    }

    progressCount.textContent = `${summary.completed_steps} / ${summary.total_steps} completed`;
    const activeIdx = INTAKE_ORDER.indexOf(summary.current_step);
    progressSteps.querySelectorAll('.step-pill').forEach((pill, idx) => {
        pill.classList.remove('active', 'done');
        if (summary.is_complete || (activeIdx !== -1 && idx < activeIdx)) {
            pill.classList.add('done');
        } else if (idx === activeIdx) {
            pill.classList.add('active');
        }
    });
}

function renderQuickReplies(chips) {
    quickRepliesEl.innerHTML = (chips || []).map((label) => (
        `<button type="button" class="chip-btn">${esc(label)}</button>`
    )).join('');
}

function renderReceipt(receipt) {
    if (!receipt) {
        receiptCard.hidden = true;
        return;
    }
    receiptCard.hidden = false;
    receiptCode.textContent = receipt.confirmation_code;
    const statusText = receipt.status === 'cancelled' ? ' (CANCELLED)' : '';
    receiptDetails.textContent =
        `${receipt.patient_name} with ${receipt.clinician} on ` +
        `${receipt.formatted_datetime}${statusText}`;
}

function renderOpenSlots(slots) {
    slotPills.innerHTML = (slots || []).map((slot) => (
        `<button type="button" class="slot-chip"
                 data-clinician="${esc(slot.clinician)}"
                 data-datetime="${esc(slot.datetime)}">${esc(slot.label)}</button>`
    )).join('');
}

function syncModeUI(mode) {
    currentMode = mode;
    modeTabs.forEach((tab) => {
        const isActive = tab.dataset.mode === mode;
        tab.classList.toggle('active', isActive);
        tab.setAttribute('aria-selected', String(isActive));
    });
    intakeProgress.hidden = (mode !== 'intake');
    chatInput.placeholder = mode === 'intake'
        ? 'Type your intake answer...'
        : 'Ask about clinic hours, location, or book/cancel an appointment...';
}

function applyPayload(data) {
    if (!data) return;
    syncModeUI(data.mode || currentMode);
    renderMessages(data.messages);
    renderSummary(data.intake_summary);
    renderQuickReplies(data.quick_replies);
    renderOpenSlots(data.available_slots);
    renderReceipt(data.last_receipt);
}

async function loadState() {
    try {
        const res = await fetch('/api/bot/state');
        if (!res.ok) throw new Error('Failed to load bot state');
        const data = await res.json();
        applyPayload(data);
    } catch (err) {
        console.error(err);
    }
}

async function sendMessage(text) {
    try {
        const res = await fetch('/api/bot/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, mode: currentMode }),
        });
        const data = await res.json();
        applyPayload(data);
        chatInput.value = '';
        chatInput.focus();
    } catch (err) {
        console.error(err);
    }
}

async function switchMode(mode) {
    if (mode === currentMode) return;
    try {
        const res = await fetch('/api/bot/mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode }),
        });
        const data = await res.json();
        applyPayload(data);
        chatInput.focus();
    } catch (err) {
        console.error(err);
    }
}

async function resetConversation() {
    try {
        const res = await fetch('/api/bot/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: currentMode }),
        });
        const data = await res.json();
        applyPayload(data);
        chatInput.value = '';
        chatInput.focus();
    } catch (err) {
        console.error(err);
    }
}

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage(chatInput.value);
});

quickRepliesEl.addEventListener('click', (e) => {
    const btn = e.target.closest('.chip-btn');
    if (!btn) return;
    const label = btn.textContent.trim();
    if (label.toLowerCase() === 'switch to ai receptionist') {
        switchMode('receptionist');
        return;
    }
    if (label.toLowerCase() === 'start new intake') {
        resetConversation();
        return;
    }
    sendMessage(label);
});

demoChips.forEach((chip) => {
    chip.addEventListener('click', () => {
        sendMessage(chip.dataset.testMsg ?? '');
    });
});

modeTabs.forEach((tab) => {
    tab.addEventListener('click', () => switchMode(tab.dataset.mode));
});

resetBtn.addEventListener('click', resetConversation);

slotPills.addEventListener('click', (e) => {
    const btn = e.target.closest('.slot-chip');
    if (!btn) return;
    qbClinician.value = btn.dataset.clinician;
    qbDatetime.value = btn.dataset.datetime.slice(0, 16);
    qbFeedback.textContent = 'Slot selected — click "Book Appointment Now" to confirm.';
    qbFeedback.classList.remove('error');
});

quickBookForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    qbFeedback.textContent = '';
    qbFeedback.classList.remove('error');

    const payload = {
        patient_name: qbPatient.value.trim(),
        clinician: qbClinician.value,
        datetime: qbDatetime.value,
        reason: qbReason.value.trim(),
    };

    try {
        const res = await fetch('/api/bot/book', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
            qbFeedback.textContent = data.error || 'Could not confirm booking.';
            qbFeedback.classList.add('error');
            return;
        }
        renderMessages(data.messages);
        renderOpenSlots(data.available_slots);
        renderReceipt(data.receipt);
        qbFeedback.textContent = `Confirmed (${data.receipt.confirmation_code}) and synced with Front Desk.`;
    } catch (err) {
        console.error(err);
        qbFeedback.textContent = 'Network error — please try again.';
        qbFeedback.classList.add('error');
    }
});

loadState();
