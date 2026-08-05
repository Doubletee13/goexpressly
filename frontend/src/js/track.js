/**
 * track.js — Public tracking page logic
 */
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('track-form');
    const input = document.getElementById('tracking-input');
    const stateLoad = document.getElementById('state-loading');
    const stateErr = document.getElementById('state-error');
    const stateRes = document.getElementById('state-results');
    const errMsg = document.getElementById('error-message');

    // Pre-fill from URL query string
    const params = new URLSearchParams(window.location.search);
    const urlId = params.get('id');
    if (urlId) {
        input.value = urlId;
        runTrack(urlId);
    }

    form.addEventListener('submit', e => {
        e.preventDefault();
        const id = input.value.trim();
        if (!id) return;
        history.replaceState(null, '', `?id=${encodeURIComponent(id)}`);
        runTrack(id);
    });

    async function runTrack(trackingId) {
        showState('loading');
        try {
            const data = await Api.trackPackage(trackingId);
            renderResults(data);
            showState('results');
        } catch (err) {
            errMsg.textContent = err.status === 404
                ? `No package found with tracking ID "${trackingId}". Please double-check and try again.`
                : (err.detail || 'A network error occurred. Please try again shortly.');
            showState('error');
        }
    }

    function showState(state) {
        stateLoad.classList.add('hidden');
        stateErr.classList.add('hidden');
        stateRes.classList.add('hidden');
        if (state === 'loading') stateLoad.classList.remove('hidden');
        if (state === 'error') stateErr.classList.remove('hidden');
        if (state === 'results') stateRes.classList.remove('hidden');
    }

    function renderResults(data) {
        // Header fields
        document.getElementById('res-tracking-id').textContent = data.tracking_id;
        document.getElementById('res-recipient').textContent = data.recipient_name;
        document.getElementById('res-origin').textContent = data.origin || '—';
        document.getElementById('res-destination').textContent = data.destination || '—';

        // Badge
        const badgeWrap = document.getElementById('res-badge-wrap');
        if (data.is_delivered) {
            badgeWrap.innerHTML = `<span class="badge badge-delivered">
        <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
        Delivered
      </span>`;
        } else if (data.current_status) {
            badgeWrap.innerHTML = `<span class="badge badge-active">
        <span class="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse-soft"></span>
        In Transit
      </span>`;
        } else {
            badgeWrap.innerHTML = `<span class="badge badge-stopped">Awaiting pickup</span>`;
        }

        // Current status highlight
        const statusWrap = document.getElementById('res-current-status-wrap');
        if (data.current_status) {
            document.getElementById('res-current-status').textContent = data.current_status;
            document.getElementById('res-current-location').textContent = data.current_location || '';
            statusWrap.classList.remove('hidden');
        } else {
            statusWrap.classList.add('hidden');
        }

        // Timeline
        const timeline = document.getElementById('res-timeline');
        const noEvents = document.getElementById('res-no-events');
        timeline.innerHTML = '';

        if (!data.history || data.history.length === 0) {
            noEvents.classList.remove('hidden');
            return;
        }

        noEvents.classList.add('hidden');
        const events = [...data.history].reverse(); // newest first

        events.forEach((evt, i) => {
            const isFirst = i === 0;
            const ts = new Date(evt.timestamp);
            const dateStr = ts.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
            const timeStr = ts.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

            const step = document.createElement('div');
            step.className = 'timeline-step';
            step.innerHTML = `
        <div class="relative">
          <div class="w-9 h-9 rounded-full flex items-center justify-center shrink-0 
            ${isFirst
                    ? 'bg-brand-500 text-white shadow-md'
                    : 'bg-white/60 dark:bg-white/10 border border-brand-200 dark:border-brand-800 text-brand-500'}">
            ${isFirst
                    ? `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>`
                    : `<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><circle cx="10" cy="10" r="4"/></svg>`}
          </div>
        </div>
        <div class="flex-1 pb-8 last:pb-0">
          <div class="flex flex-wrap items-start justify-between gap-2 mb-1">
            <p class="font-semibold text-slate-800 dark:text-slate-100 text-sm">${escHtml(evt.status_label)}</p>
            <span class="text-xs text-slate-400 shrink-0">${dateStr} · ${timeStr}</span>
          </div>
          ${evt.location ? `<p class="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2C8.686 2 6 4.686 6 8c0 5.25 6 13 6 13s6-7.75 6-13c0-3.314-2.686-6-6-6z"/></svg>
            ${escHtml(evt.location)}</p>` : ''}
        </div>`;
            timeline.appendChild(step);
        });
    }

    function escHtml(str) {
        return String(str).replace(/[&<>"']/g, m =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
    }
});
