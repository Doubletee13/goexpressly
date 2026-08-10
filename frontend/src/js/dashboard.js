/**
 * dashboard.js — Admin dashboard logic (v3)
 * Features: live autocomplete, toast notifications, event-location sync
 */
document.addEventListener('DOMContentLoaded', async () => {
    // ── Auth guard ──────────────────────────────────────────────────────────
    if (!Api.isAuthenticated()) { window.location.href = 'login.html'; return; }

    try {
        const me = await Api.getMe();
        document.getElementById('admin-email').textContent = me.email || 'Admin';
    } catch { Api.logout(); return; }

    // ── State ────────────────────────────────────────────────────────────────
    let currentPage = 1;
    const pageSize = 20;

    // ── Sidebar (mobile) ─────────────────────────────────────────────────────
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    function openSidebar() { sidebar.classList.remove('-translate-x-full'); sidebarOverlay.classList.remove('hidden'); }
    function closeSidebar() { sidebar.classList.add('-translate-x-full'); sidebarOverlay.classList.add('hidden'); }
    sidebarToggle.addEventListener('click', openSidebar);
    sidebarOverlay.addEventListener('click', closeSidebar);

    // ── Logout ───────────────────────────────────────────────────────────────
    document.getElementById('logout-btn').addEventListener('click', () => Api.logout());

    // ── Modals ───────────────────────────────────────────────────────────────
    function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
    function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => closeModal(btn.dataset.modal));
    });
    ['modal-create', 'modal-event', 'modal-delete'].forEach(id => {
        document.getElementById(id).addEventListener('click', e => {
            if (e.target === e.currentTarget) closeModal(id);
        });
    });

    // ── Toast notification ───────────────────────────────────────────────────
    function showToast(message, type = 'success') {
        const icon = type === 'success'
            ? `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>`
            : `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
        const color = type === 'success'
            ? 'bg-green-500/15 text-green-500'
            : 'bg-red-500/15 text-red-500';

        const toast = document.createElement('div');
        toast.className = 'fixed bottom-6 right-6 z-[9999] glass px-5 py-4 rounded-xl flex items-center gap-3 shadow-xl transition-all duration-300 translate-y-4 opacity-0 max-w-xs';
        toast.innerHTML = `
            <div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${color}">${icon}</div>
            <p class="text-sm font-semibold text-slate-800 dark:text-slate-100 leading-snug">${esc(message)}</p>
            <button class="ml-auto text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 shrink-0" onclick="this.parentElement.remove()">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>`;
        document.body.appendChild(toast);
        requestAnimationFrame(() => {
            setTimeout(() => toast.classList.remove('translate-y-4', 'opacity-0'), 10);
        });
        setTimeout(() => {
            toast.classList.add('translate-y-4', 'opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    // ── Location Autocomplete ─────────────────────────────────────────────────
    /**
     * initAutocomplete - attaches a live Nominatim autocomplete dropdown to a
     * location text input.
     *
     * @param {Object} opts
     *   inputId    - id of the text input
     *   dropdownId - id of the <ul> dropdown element
     *   latId      - id of the hidden lat input
     *   lngId      - id of the hidden lng input
     *   statusId   - id of the status <p> element
     *   onSelect   - optional callback called with the chosen Nominatim result
     */
    function initAutocomplete({ inputId, dropdownId, latId, lngId, statusId, onSelect }) {
        const input = document.getElementById(inputId);
        const dropdown = document.getElementById(dropdownId);
        const latEl = document.getElementById(latId);
        const lngEl = document.getElementById(lngId);
        const statusEl = document.getElementById(statusId);
        let timer = null;
        let activeIndex = -1;
        let results = [];

        input.setAttribute('autocomplete', 'off');

        // Debounced input handler
        input.addEventListener('input', () => {
            clearTimeout(timer);
            const val = input.value.trim();
            if (latEl) latEl.value = '';
            if (lngEl) lngEl.value = '';
            if (val.length < 3) { hideDropdown(); return; }
            if (statusEl) {
                statusEl.textContent = '';
                statusEl.className = 'text-xs mt-1 font-medium text-slate-400';
            }
            timer = setTimeout(() => fetchSuggestions(val), 420);
        });

        // Keyboard navigation
        input.addEventListener('keydown', e => {
            const items = dropdown.querySelectorAll('li[data-idx]');
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                activeIndex = Math.min(activeIndex + 1, items.length - 1);
                updateActive(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                activeIndex = Math.max(activeIndex - 1, 0);
                updateActive(items);
            } else if (e.key === 'Enter') {
                if (activeIndex >= 0 && results[activeIndex]) {
                    e.preventDefault();
                    selectResult(results[activeIndex]);
                }
            } else if (e.key === 'Escape') {
                hideDropdown();
            }
        });

        function updateActive(items) {
            items.forEach((li, i) => {
                li.classList.toggle('bg-brand-50/60', i === activeIndex);
                li.classList.toggle('dark:bg-brand-900/20', i === activeIndex);
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', e => {
            if (!input.contains(e.target) && !dropdown.contains(e.target)) hideDropdown();
        });

        async function fetchSuggestions(query) {
            try {
                const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=5&addressdetails=1`;
                const res = await fetch(url, { headers: { 'Accept-Language': 'en' } });
                results = await res.json();
                renderDropdown(results);
            } catch { hideDropdown(); }
        }

        function renderDropdown(items) {
            dropdown.innerHTML = '';
            activeIndex = -1;

            if (!items.length) {
                dropdown.innerHTML = `<li class="px-4 py-3 text-sm text-slate-400 italic">No locations found. Try a different search.</li>`;
                showDropdown();
                return;
            }

            items.forEach((item, i) => {
                const li = document.createElement('li');
                li.dataset.idx = i;
                li.className = 'px-4 py-3 text-sm cursor-pointer hover:bg-brand-50/60 dark:hover:bg-brand-900/20 border-b border-white/10 last:border-0 transition-colors';
                const parts = item.display_name.split(',');
                const short = parts.slice(0, 3).join(', ');
                const region = parts.slice(-2).join(', ').trim();
                li.innerHTML = `
                    <p class="font-semibold text-slate-800 dark:text-slate-100 truncate leading-snug">${esc(short)}</p>
                    <p class="text-xs text-slate-400 mt-0.5 truncate">${esc(region)}</p>`;
                li.addEventListener('mousedown', e => {
                    e.preventDefault(); // prevent blur before click
                    selectResult(item);
                });
                dropdown.appendChild(li);
            });
            showDropdown();
        }

        function selectResult(item) {
            const short = item.display_name.split(',').slice(0, 3).join(', ');
            input.value = short;
            if (latEl) latEl.value = parseFloat(item.lat).toFixed(6);
            if (lngEl) lngEl.value = parseFloat(item.lon).toFixed(6);
            if (statusEl) {
                statusEl.textContent = `✓ Located: ${short}`;
                statusEl.className = 'text-xs mt-1 font-medium text-emerald-600 dark:text-emerald-400';
            }
            hideDropdown();
            if (onSelect) onSelect(item, short);
        }

        function showDropdown() { dropdown.classList.remove('hidden'); }
        function hideDropdown() {
            dropdown.classList.add('hidden');
            dropdown.innerHTML = '';
            activeIndex = -1;
            results = [];
        }

    }

    // Initialise autocomplete for Create Package modal (Origin)
    initAutocomplete({
        inputId: 'create-location-input',
        dropdownId: 'create-location-dropdown',
        latId: 'create-lat',
        lngId: 'create-lng',
        statusId: 'create-geocode-status',
    });

    // Initialise autocomplete for Create Package modal (Destination)
    initAutocomplete({
        inputId: 'create-destination-input',
        dropdownId: 'create-destination-dropdown',
    });

    // Initialise autocomplete for Create Package modal (City Collection)
    initAutocomplete({
        inputId: 'create-citycollection-input',
        dropdownId: 'create-citycollection-dropdown',
    });

    // Initialise autocomplete for Add Event modal (Location)
    initAutocomplete({
        inputId: 'event-location-input',
        dropdownId: 'event-location-dropdown',
        latId: 'event-lat',
        lngId: 'event-lng',
        statusId: 'event-geocode-status',
    });

    // ── Load packages ────────────────────────────────────────────────────────
    async function loadPackages(page = 1) {
        const tbody = document.getElementById('packages-table-body');
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-14 text-slate-400">
            <div class="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            Loading...</td></tr>`;
        try {
            const data = await Api.listPackages(page, pageSize);
            renderTable(data.items || []);
            updatePagination(data);
            updateStats(data);
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center py-14 text-red-500 text-sm">${err.detail || 'Failed to load packages.'}</td></tr>`;
        }
    }

    function updateStats(data) {
        const total = data.total || 0;
        const items = data.items || [];
        const delivered = items.filter(p => p.is_delivered).length;
        const transit = items.filter(p => !p.is_delivered && p.current_status).length;
        document.getElementById('stat-total').textContent = total;
        document.getElementById('stat-transit').textContent = transit;
        document.getElementById('stat-delivered').textContent = delivered;
        document.getElementById('stat-page').textContent = items.length;
    }

    function updatePagination(data) {
        const total = data.total || 0;
        const totalPages = Math.ceil(total / pageSize) || 1;
        document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages}`;
        document.getElementById('prev-page').disabled = currentPage <= 1;
        document.getElementById('next-page').disabled = currentPage >= totalPages;
    }

    document.getElementById('prev-page').addEventListener('click', () => { currentPage--; loadPackages(currentPage); });
    document.getElementById('next-page').addEventListener('click', () => { currentPage++; loadPackages(currentPage); });

    function renderTable(packages) {
        const tbody = document.getElementById('packages-table-body');
        if (!packages.length) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center py-14 text-slate-400 text-sm">No packages found. Create your first one!</td></tr>`;
            return;
        }
        tbody.innerHTML = packages.map(pkg => `
            <tr class="border-t border-white/10 dark:border-white/5 hover:bg-white/20 dark:hover:bg-white/5 transition-colors group">
                <td class="px-5 py-4"><span class="tracking-chip text-xs">${esc(pkg.tracking_id)}</span></td>
                <td class="px-5 py-4 hidden sm:table-cell">
                    <p class="font-medium text-slate-700 dark:text-slate-200 text-sm">${esc(pkg.recipient_name)}</p>
                    <p class="text-xs text-slate-400">${esc(pkg.recipient_email)}</p>
                </td>
                <td class="px-5 py-4 hidden md:table-cell">${renderBadge(pkg)}</td>
                <td class="px-5 py-4 hidden lg:table-cell text-slate-500 dark:text-slate-400 text-sm">${esc(pkg.destination || '—')}</td>
                <td class="px-5 py-4 text-right">
                    <div class="flex items-center justify-end gap-1">
                        <button class="add-event-btn glass p-2 rounded-lg text-brand-500 hover:bg-brand-50/50 dark:hover:bg-brand-900/20 transition-all"
                            data-id="${esc(pkg.id)}" data-tracking="${esc(pkg.tracking_id)}" title="Add tracking event">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
                        </button>
                        <button class="delete-btn glass p-2 rounded-lg text-red-500 hover:bg-red-50/50 dark:hover:bg-red-900/20 transition-all"
                            data-id="${esc(pkg.id)}" data-tracking="${esc(pkg.tracking_id)}" title="Delete package">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/></svg>
                        </button>
                    </div>
                </td>
            </tr>`).join('');

        tbody.querySelectorAll('.add-event-btn').forEach(btn =>
            btn.addEventListener('click', () => openAddEventModal(btn.dataset.id, btn.dataset.tracking)));
        tbody.querySelectorAll('.delete-btn').forEach(btn =>
            btn.addEventListener('click', () => openDeleteModal(btn.dataset.id, btn.dataset.tracking)));
    }

    function renderBadge(pkg) {
        if (pkg.is_delivered) return `<span class="badge badge-delivered">Delivered</span>`;
        if (pkg.current_status) return `<span class="badge badge-active">${esc(pkg.current_status)}</span>`;
        return `<span class="badge bg-slate-100 dark:bg-slate-800 text-slate-500">Pending</span>`;
    }

    // ── Create Package ────────────────────────────────────────────────────────
    document.getElementById('create-package-btn').addEventListener('click', () => {
        document.getElementById('form-create').reset();
        document.getElementById('create-error').classList.add('hidden');
        document.getElementById('create-location-input').value = '';
        document.getElementById('create-destination-input').value = '';
        document.getElementById('create-citycollection-input').value = '';
        document.getElementById('create-lat').value = '';
        document.getElementById('create-lng').value = '';
        document.getElementById('create-geocode-status').textContent = '';
        openModal('modal-create');
    });

    document.getElementById('form-create').addEventListener('submit', async e => {
        e.preventDefault();
        const form = e.target;
        const errEl = document.getElementById('create-error');
        const btn = form.querySelector('button[type=submit]');
        btn.disabled = true; btn.textContent = 'Creating...';
        errEl.classList.add('hidden');

        const body = {};
        new FormData(form).forEach((v, k) => { if (v !== '') body[k] = v; });

        try {
            const pkg = await Api.createPackage(body);
            closeModal('modal-create');
            loadPackages(currentPage);
            showToast(`Package created! Tracking ID: ${pkg.tracking_id || 'See table'}`);
        } catch (err) {
            errEl.textContent = err.detail || 'Failed to create package.';
            errEl.classList.remove('hidden');
        } finally {
            btn.disabled = false; btn.textContent = 'Create Package';
        }
    });

    // ── Add Tracking Event ────────────────────────────────────────────────────
    function openAddEventModal(pkgId, trackingId) {
        document.getElementById('form-event').reset();
        document.getElementById('event-pkg-uuid').value = pkgId;
        document.getElementById('event-pkg-id').textContent = trackingId;
        document.getElementById('event-error').classList.add('hidden');
        document.getElementById('event-location-input').value = '';
        document.getElementById('event-lat').value = '';
        document.getElementById('event-lng').value = '';
        document.getElementById('event-geocode-status').textContent = '';
        openModal('modal-event');
    }

    document.getElementById('form-event').addEventListener('submit', async e => {
        e.preventDefault();
        const form = e.target;
        const pkgId = document.getElementById('event-pkg-uuid').value;
        const errEl = document.getElementById('event-error');
        const btn = form.querySelector('button[type=submit]');
        btn.disabled = true; btn.textContent = 'Adding...';
        errEl.classList.add('hidden');

        const body = {};
        new FormData(form).forEach((v, k) => { if (v !== '') body[k] = v; });
        body.is_delivered = document.getElementById('is-delivered').checked;
        delete body.event_pkg_uuid;

        try {
            await Api.addEvent(pkgId, body);
            closeModal('modal-event');
            loadPackages(currentPage);
            showToast('Tracking event added successfully!');
        } catch (err) {
            errEl.textContent = err.detail || 'Failed to add event.';
            errEl.classList.remove('hidden');
        } finally {
            btn.disabled = false; btn.textContent = 'Add Event';
        }
    });

    // ── Delete Package ────────────────────────────────────────────────────────
    function openDeleteModal(pkgId, trackingId) {
        document.getElementById('delete-pkg-uuid').value = pkgId;
        document.getElementById('delete-pkg-id').textContent = trackingId;
        openModal('modal-delete');
    }

    document.getElementById('confirm-delete-btn').addEventListener('click', async () => {
        const pkgId = document.getElementById('delete-pkg-uuid').value;
        const btn = document.getElementById('confirm-delete-btn');
        btn.disabled = true; btn.textContent = 'Deleting...';
        try {
            await Api.deletePackage(pkgId);
            closeModal('modal-delete');
            loadPackages(currentPage);
            showToast('Package deleted.');
        } catch (err) {
            showToast(err.detail || 'Failed to delete package.', 'error');
        } finally {
            btn.disabled = false; btn.textContent = 'Delete';
        }
    });

    // ── Escape helper ──────────────────────────────────────────────────────────
    function esc(str) {
        return String(str || '').replace(/[&<>"']/g, m =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
    }

    // ── Init ────────────────────────────────────────────────────────────────────
    loadPackages(1);
});
