/**
 * dashboard.js — Admin dashboard logic
 */
document.addEventListener('DOMContentLoaded', async () => {
    // Auth guard
    if (!Api.isAuthenticated()) { window.location.href = 'login.html'; return; }

    // Load admin info
    try {
        const me = await Api.getMe();
        document.getElementById('admin-email').textContent = me.email || 'Admin';
    } catch { Api.logout(); return; }

    // ── State ──────────────────────────────────────────────────────
    let currentPage = 1;
    const pageSize = 20;

    // ── Sidebar (mobile) ───────────────────────────────────────────
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarOverlay = document.getElementById('sidebar-overlay');

    function openSidebar() {
        sidebar.classList.remove('-translate-x-full');
        sidebarOverlay.classList.remove('hidden');
    }
    function closeSidebar() {
        sidebar.classList.add('-translate-x-full');
        sidebarOverlay.classList.add('hidden');
    }
    sidebarToggle.addEventListener('click', openSidebar);
    sidebarOverlay.addEventListener('click', closeSidebar);

    // ── Logout ─────────────────────────────────────────────────────
    document.getElementById('logout-btn').addEventListener('click', () => Api.logout());

    // ── Modals ──────────────────────────────────────────────────────
    function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
    function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => closeModal(btn.dataset.modal));
    });
    // Close on backdrop click
    ['modal-create', 'modal-event', 'modal-delete'].forEach(id => {
        document.getElementById(id).addEventListener('click', e => {
            if (e.target === e.currentTarget) closeModal(id);
        });
    });

    // ── Load packages ───────────────────────────────────────────────
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
        <td class="px-5 py-4">
          <span class="tracking-chip text-xs">${esc(pkg.tracking_id)}</span>
        </td>
        <td class="px-5 py-4 hidden sm:table-cell">
          <p class="font-medium text-slate-700 dark:text-slate-200 text-sm">${esc(pkg.recipient_name)}</p>
          <p class="text-xs text-slate-400">${esc(pkg.recipient_email)}</p>
        </td>
        <td class="px-5 py-4 hidden md:table-cell">${renderBadge(pkg)}</td>
        <td class="px-5 py-4 hidden lg:table-cell text-slate-500 dark:text-slate-400 text-sm">${esc(pkg.destination || '—')}</td>
        <td class="px-5 py-4 text-right">
          <div class="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
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
      </tr>
    `).join('');

        // Bind row action buttons
        tbody.querySelectorAll('.add-event-btn').forEach(btn => {
            btn.addEventListener('click', () => openAddEventModal(btn.dataset.id, btn.dataset.tracking));
        });
        tbody.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => openDeleteModal(btn.dataset.id, btn.dataset.tracking));
        });
    }

    function renderBadge(pkg) {
        if (pkg.is_delivered) return `<span class="badge badge-delivered">Delivered</span>`;
        if (pkg.current_status) return `<span class="badge badge-active">${esc(pkg.current_status)}</span>`;
        return `<span class="badge bg-slate-100 dark:bg-slate-800 text-slate-500">Pending</span>`;
    }

    // ── Create Package ─────────────────────────────────────────────
    document.getElementById('create-package-btn').addEventListener('click', () => {
        document.getElementById('form-create').reset();
        document.getElementById('create-error').classList.add('hidden');
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
        new FormData(form).forEach((v, k) => { if (v) body[k] = v; });

        try {
            await Api.createPackage(body);
            closeModal('modal-create');
            loadPackages(currentPage);
        } catch (err) {
            errEl.textContent = err.detail || 'Failed to create package.';
            errEl.classList.remove('hidden');
        } finally {
            btn.disabled = false; btn.textContent = 'Create Package';
        }
    });

    // ── Add Tracking Event ─────────────────────────────────────────
    function openAddEventModal(pkgId, trackingId) {
        document.getElementById('form-event').reset();
        document.getElementById('event-pkg-uuid').value = pkgId;
        document.getElementById('event-pkg-id').textContent = trackingId;
        document.getElementById('event-error').classList.add('hidden');
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
        new FormData(form).forEach((v, k) => { if (v) body[k] = v; });
        body.is_delivered = document.getElementById('is-delivered').checked;
        delete body.event_pkg_uuid;

        try {
            await Api.addEvent(pkgId, body);
            closeModal('modal-event');
            loadPackages(currentPage);
        } catch (err) {
            errEl.textContent = err.detail || 'Failed to add event.';
            errEl.classList.remove('hidden');
        } finally {
            btn.disabled = false; btn.textContent = 'Add Event';
        }
    });

    // ── Delete Package ─────────────────────────────────────────────
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
        } catch (err) {
            alert(err.detail || 'Failed to delete package.');
        } finally {
            btn.disabled = false; btn.textContent = 'Delete';
        }
    });

    // ── Escape helper ──────────────────────────────────────────────
    function esc(str) {
        return String(str || '').replace(/[&<>"']/g, m =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
    }

    // ── Init ──────────────────────────────────────────────────────
    loadPackages(1);
});
