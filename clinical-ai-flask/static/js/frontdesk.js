const queueBody = document.querySelector('#queue-table tbody');
const allBody = document.querySelector('#all-table tbody');
const form = document.getElementById('appt-form');
const formMsg = document.getElementById('form-msg');

const modal = document.getElementById('reschedule-modal');
const modalForm = document.getElementById('reschedule-form');
const modalInput = document.getElementById('new-datetime');
const modalMsg = document.getElementById('modal-msg');
const modalName = document.getElementById('modal-patient-name');
const modalCancelBtn = document.getElementById('modal-cancel-btn');
let currentRescheduleId = null;

const cancelModal = document.getElementById('cancel-modal');
const cancelName = document.getElementById('cancel-patient-name');
const cancelModalBtn = document.getElementById('cancel-modal-btn');
const confirmCancelBtn = document.getElementById('confirm-cancel-btn');
let currentCancelId = null;

function setMessage(text, isError = false) {
    formMsg.textContent = text;
    formMsg.classList.toggle('error', isError);
}

function formatDateTime(iso) {
    const d = new Date(iso);
    return d.toLocaleString([], {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function formatTime(iso) {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function emptyRow(colspan, text) {
    return `<tr class="empty-row"><td colspan="${colspan}">${text}</td></tr>`;
}

function esc(str) {
    const div = document.createElement('div');
    div.textContent = str ?? '';
    return div.innerHTML;
}

function renderQueue(rows) {
    if (!rows.length) {
        queueBody.innerHTML = emptyRow(5, 'No appointments scheduled for today.');
        return;
    }
    queueBody.innerHTML = rows.map(a => `
        <tr>
            <td>${formatTime(a.datetime)}</td>
            <td>${esc(a.patient_name)}</td>
            <td>${esc(a.clinician)}</td>
            <td>${esc(a.reason) || '—'}</td>
            <td>
                <button class="row-btn" data-id="${a.id}" data-action="reschedule">Reschedule</button>
                <button class="row-btn danger" data-id="${a.id}" data-action="cancel">Cancel</button>
            </td>
        </tr>
    `).join('');
}

function renderAll(rows) {
    if (!rows.length) {
        allBody.innerHTML = emptyRow(6, 'No appointments yet.');
        return;
    }
    const sorted = [...rows].sort((a, b) => new Date(b.datetime) - new Date(a.datetime));
    allBody.innerHTML = sorted.map(a => {
        const cancelled = a.status === 'cancelled';
        const actions = cancelled
            ? '<span class="panel-hint">—</span>'
            : `<button class="row-btn" data-id="${a.id}" data-action="reschedule">Reschedule</button>
               <button class="row-btn danger" data-id="${a.id}" data-action="cancel">Cancel</button>`;
        return `
            <tr>
                <td>${formatDateTime(a.datetime)}</td>
                <td>${esc(a.patient_name)}</td>
                <td>${esc(a.clinician)}</td>
                <td>${esc(a.reason) || '—'}</td>
                <td><span class="status-pill ${cancelled ? 'cancelled' : ''}">${a.status}</span></td>
                <td>${actions}</td>
            </tr>
        `;
    }).join('');
}

async function loadAll() {
    try {
        const [qRes, aRes] = await Promise.all([
            fetch('/api/appointments/queue'),
            fetch('/api/appointments'),
        ]);
        if (!qRes.ok || !aRes.ok) throw new Error('Failed to load appointments');
        const [queue, all] = await Promise.all([qRes.json(), aRes.json()]);
        renderQueue(queue);
        renderAll(all);
    } catch (err) {
        console.error(err);
        queueBody.innerHTML = emptyRow(5, 'Could not load the queue.');
        allBody.innerHTML = emptyRow(6, 'Could not load appointments.');
    }
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    setMessage('');
    const payload = Object.fromEntries(new FormData(form));

    try {
        const res = await fetch('/api/appointments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
            setMessage(data.error || 'Could not schedule appointment.', true);
            return;
        }
        setMessage('Appointment scheduled.');
        form.reset();
        loadAll();
    } catch (err) {
        console.error(err);
        setMessage('Network error — please try again.', true);
    }
});

async function handleAction(e) {
    const btn = e.target.closest('button[data-action]');
    if (!btn) return;
    const id = btn.dataset.id;
    const action = btn.dataset.action;

    if (action === 'cancel') {
        const row = btn.closest('tr');
        const patientName = row.cells[1].textContent; 
        
        currentCancelId = id;
        cancelName.textContent = patientName;
        cancelModal.hidden = false;
    }

    if (action === 'reschedule') {
        const row = btn.closest('tr');
        const patientName = row.cells[1].textContent; 
        
        currentRescheduleId = id;
        modalName.textContent = `Patient: ${patientName}`;
        modalInput.value = ''; 
        modalMsg.textContent = ''; 
        modal.hidden = false; 
        
        setTimeout(() => modalInput.focus(), 50);
    }
}

queueBody.addEventListener('click', handleAction);
allBody.addEventListener('click', handleAction);

modalForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const newDatetime = modalInput.value;
    
    try {
        const res = await fetch(`/api/appointments/${currentRescheduleId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ datetime: newDatetime }),
        });
        const data = await res.json();
        
        if (!res.ok) {
            modalMsg.textContent = data.error || 'Could not reschedule.';
            return;
        }
        
        modal.hidden = true;
        setMessage('Appointment rescheduled.');
        loadAll();
    } catch (err) {
        console.error(err);
        modalMsg.textContent = 'Network error — please try again.';
    }
});

modalCancelBtn.addEventListener('click', () => {
    modal.hidden = true;
});

modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.hidden = true;
});

cancelModalBtn.addEventListener('click', () => {
    cancelModal.hidden = true;
});

confirmCancelBtn.addEventListener('click', async () => {
    try {
        const res = await fetch(`/api/appointments/${currentCancelId}`, { method: 'DELETE' });
        if (!res.ok) {
            const data = await res.json();
            setMessage(data.error || 'Could not cancel.', true);
            return;
        }
        cancelModal.hidden = true;
        setMessage('Appointment cancelled.');
        loadAll();
    } catch (err) {
        console.error(err);
        setMessage('Network error — please try again.', true);
        cancelModal.hidden = true;
    }
});

cancelModal.addEventListener('click', (e) => {
    if (e.target === cancelModal) cancelModal.hidden = true;
});

loadAll();