/**
 * track.js — Public tracking page logic (v3)
 * Map: Voyager tiles (light), OSM (dark), zoom-10, pulsing marker, theme-aware popup
 */
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('track-form');
    const input = document.getElementById('tracking-input');
    const stateLoad = document.getElementById('state-loading');
    const stateErr = document.getElementById('state-error');
    const stateRes = document.getElementById('state-results');
    const errMsg = document.getElementById('error-message');

    let mapInstance = null;
    let mapMarker = null;
    let mapTileLayer = null;

    // Theme change listener — update tiles if map already loaded
    const themeObserver = new MutationObserver(() => {
        if (mapInstance && mapTileLayer) updateMapTiles();
    });
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

    // Pre-fill from URL query param
    const params = new URLSearchParams(window.location.search);
    const urlId = params.get('id');
    if (urlId) { input.value = urlId; runTrack(urlId); }

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

    // ── Helpers ────────────────────────────────────────────────────────────────

    function setText(id, val, fallback = '—') {
        const el = document.getElementById(id);
        if (el) el.textContent = val || fallback;
    }

    function fmtDate(isoStr) {
        if (!isoStr) return null;
        try { return new Date(isoStr).toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: 'numeric' }); }
        catch { return isoStr; }
    }

    function fmtDateTime(isoStr) {
        if (!isoStr) return null;
        try {
            return new Date(isoStr).toLocaleString('en-GB', {
                year: 'numeric', month: 'short', day: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
        } catch { return isoStr; }
    }

    function escHtml(str) {
        return String(str || '').replace(/[&<>"']/g, m =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
    }

    // ── Main render ────────────────────────────────────────────────────────────

    function renderResults(data) {
        setText('res-tracking-id', data.tracking_id);
        setText('res-recipient', data.recipient_name);
        setText('res-origin', data.origin);
        setText('res-destination', data.destination);

        // Status bar + badge
        const bar = document.getElementById('res-status-bar');
        const badgeWrap = document.getElementById('res-badge-wrap');

        if (data.is_delivered) {
            bar.className = 'h-1.5 bg-gradient-to-r from-green-400 to-emerald-500 w-full';
            badgeWrap.innerHTML = `<span class="badge badge-delivered">
              <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
              Delivered</span>`;
        } else if (data.current_status) {
            bar.className = 'h-1.5 bg-gradient-to-r from-brand-400 to-brand-600 w-full';
            badgeWrap.innerHTML = `<span class="badge badge-active">
              <span class="w-1.5 h-1.5 rounded-full bg-brand-500 animate-pulse-soft inline-block"></span>
              In Transit</span>`;
        } else {
            bar.className = 'h-1.5 bg-gradient-to-r from-amber-400 to-orange-400 w-full';
            badgeWrap.innerHTML = `<span class="badge badge-stopped">Awaiting Pickup</span>`;
        }

        renderProgress(data);

        const statusWrap = document.getElementById('res-current-status-wrap');
        if (data.current_status) {
            setText('res-current-status', data.current_status);
            setText('res-current-location', data.current_location, '');
            statusWrap.classList.remove('hidden');
        } else {
            statusWrap.classList.add('hidden');
        }

        renderMap(data.current_lat, data.current_lng);

        // Sender section
        const senderSection = document.getElementById('sender-section');
        const hasSender = data.sender_name || data.city_collection || data.origin ||
            data.shipping_date || data.carrier || data.sender_address ||
            data.shipping_quantity != null || data.weight_lbs != null;
        if (hasSender) {
            setText('res-city-collection', data.city_collection);
            setText('res-origin-city', data.origin);
            setText('res-shipping-date', fmtDate(data.shipping_date));
            setText('res-carrier', data.carrier);
            setText('res-sender-name', data.sender_name);
            setText('res-sender-address', data.sender_address);
            setText('res-shipping-qty', data.shipping_quantity != null ? String(data.shipping_quantity) : null);
            setText('res-weight', data.weight_lbs != null ? String(data.weight_lbs) : null);
            senderSection.classList.remove('hidden');
        } else {
            senderSection.classList.add('hidden');
        }

        // Recipient section
        const recipientSection = document.getElementById('recipient-section');
        const hasRecipient = data.delivery_city || data.destination ||
            data.destination_address || data.estimated_delivery_date || data.recipient_name;
        if (hasRecipient) {
            setText('res-delivery-city', data.delivery_city);
            setText('res-dest-city', data.destination);
            setText('res-dest-shipping-time', data.carrier);
            setText('res-delivery-time', fmtDateTime(data.estimated_delivery_date));
            setText('res-recipient-name', data.recipient_name);
            setText('res-dest-address', data.destination_address);
            recipientSection.classList.remove('hidden');
        } else {
            recipientSection.classList.add('hidden');
        }

        const grid = document.getElementById('sender-recipient-grid');
        if (hasSender || hasRecipient) grid.classList.remove('hidden');
        else grid.classList.add('hidden');

        renderTimeline(data.history || []);
    }

    // ── Progress stepper ───────────────────────────────────────────────────────

    function renderProgress(data) {
        const wrap = document.getElementById('res-progress');
        wrap.classList.remove('hidden');

        const steps = wrap.querySelectorAll('.progress-step');
        const dots = wrap.querySelectorAll('.progress-dot');

        let active = 0;
        if (data.is_delivered) active = 3;
        else if (data.current_status) {
            const s = (data.current_status || '').toLowerCase();
            if (s.includes('deliver') || s.includes('out for')) active = 2;
            else active = 1;
        }

        steps.forEach((step, i) => {
            const dot = dots[i];
            if (i < active) {
                dot.style.borderColor = '#3B9EBF';
                dot.style.background = '#3B9EBF';
                dot.querySelector('div').style.background = '#fff';
                step.classList.add('done');
            } else if (i === active) {
                dot.style.borderColor = '#3B9EBF';
                dot.style.background = 'rgba(59,158,191,0.15)';
                dot.querySelector('div').style.background = '#3B9EBF';
                step.classList.remove('done');
            } else {
                dot.style.borderColor = 'rgba(148,163,184,0.4)';
                dot.style.background = 'transparent';
                dot.querySelector('div').style.background = 'rgba(148,163,184,0.3)';
                step.classList.remove('done');
            }
        });
    }

    // ── Timeline ───────────────────────────────────────────────────────────────

    function renderTimeline(history) {
        const tl = document.getElementById('res-timeline');
        const noEvents = document.getElementById('res-no-events');
        tl.innerHTML = '';

        if (!history.length) { noEvents.classList.remove('hidden'); return; }
        noEvents.classList.add('hidden');

        const events = [...history].reverse();
        events.forEach((evt, i) => {
            const isFirst = i === 0;
            const ts = new Date(evt.timestamp);
            const dateStr = ts.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
            const timeStr = ts.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

            const item = document.createElement('div');
            item.className = 'tl-item flex gap-4 pb-7';
            item.innerHTML = `
              <div class="shrink-0 flex flex-col items-center" style="width:40px">
                <div class="w-9 h-9 rounded-full flex items-center justify-center shadow-sm transition-all ${isFirst
                    ? 'bg-brand-500 text-white'
                    : 'bg-white/60 dark:bg-white/10 border border-brand-200 dark:border-white/10 text-brand-400'
                }">
                  ${isFirst
                    ? `<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>`
                    : `<span class="w-2 h-2 rounded-full bg-current block"></span>`}
                </div>
              </div>
              <div class="flex-1 min-w-0 pt-1">
                <div class="flex flex-wrap items-start justify-between gap-x-4 gap-y-1 mb-1.5">
                  <p class="font-bold text-slate-800 dark:text-slate-100 text-sm leading-snug">${escHtml(evt.status_label)}</p>
                  <span class="text-[11px] text-slate-400 shrink-0 tabular-nums">${dateStr} · ${timeStr}</span>
                </div>
                ${evt.location ? `
                  <p class="text-xs text-brand-500 dark:text-brand-400 flex items-center gap-1.5">
                    <svg class="w-3 h-3 shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2C8.686 2 6 4.686 6 8c0 5.25 6 13 6 13s6-7.75 6-13c0-3.314-2.686-6-6-6z"/></svg>
                    ${escHtml(evt.location)}
                  </p>` : ''}
              </div>`;
            tl.appendChild(item);
        });
    }

    // ── Map ────────────────────────────────────────────────────────────────────

    function isDarkMode() {
        return document.documentElement.classList.contains('dark');
    }

    function getTileConfig() {
        if (isDarkMode()) {
            return {
                url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            };
        }
        return {
            url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>'
        };
    }

    function updateMapTiles() {
        if (!mapInstance) return;
        if (mapTileLayer) { mapInstance.removeLayer(mapTileLayer); mapTileLayer = null; }
        const cfg = getTileConfig();
        mapTileLayer = L.tileLayer(cfg.url, { maxZoom: 19, attribution: cfg.attribution });
        mapTileLayer.addTo(mapInstance);
    }

    function getPopupStyle() {
        return isDarkMode()
            ? 'background:rgba(15,22,35,0.95);color:#e2ebf5;border:1px solid rgba(59,158,191,0.4);border-radius:12px;'
            : 'background:rgba(255,255,255,0.95);color:#1e293b;border:1px solid rgba(59,158,191,0.35);border-radius:12px;';
    }

    function renderMap(lat, lng) {
        const section = document.getElementById('map-section');
        const noCoords = document.getElementById('map-no-coords');
        const mapCanvas = document.getElementById('map-canvas');

        if (!lat || !lng) {
            // Show fallback, hide map canvas
            section.classList.remove('hidden');
            if (mapCanvas) mapCanvas.style.display = 'none';
            if (noCoords) noCoords.classList.remove('hidden');
            return;
        }

        // Hide fallback, show map canvas
        if (mapCanvas) mapCanvas.style.display = '';
        if (noCoords) noCoords.classList.add('hidden');
        section.classList.remove('hidden');

        const tryInit = setInterval(() => {
            if (typeof L === 'undefined') return;
            clearInterval(tryInit);

            const pos = [parseFloat(lat), parseFloat(lng)];

            if (!mapInstance) {
                mapInstance = L.map('map-canvas', {
                    zoomControl: true,
                    scrollWheelZoom: false,
                    attributionControl: true,
                });
                mapInstance.setView(pos, 10);
                const cfg = getTileConfig();
                mapTileLayer = L.tileLayer(cfg.url, { maxZoom: 19, attribution: cfg.attribution });
                mapTileLayer.addTo(mapInstance);
            } else {
                mapInstance.setView(pos, 10);
                updateMapTiles();
            }

            // Fix rendering after being hidden
            setTimeout(() => { if (mapInstance) mapInstance.invalidateSize(); }, 120);

            // Remove old marker
            if (mapMarker) { mapInstance.removeLayer(mapMarker); mapMarker = null; }

            // Custom pulsing HTML marker
            const icon = L.divIcon({
                className: '',
                html: `<div class="pkg-marker-wrap">
                         <div class="pkg-marker-pulse"></div>
                         <div class="pkg-marker-dot"></div>
                       </div>`,
                iconSize: [48, 48],
                iconAnchor: [24, 24],
                popupAnchor: [0, -28],
            });

            mapMarker = L.marker(pos, { icon }).addTo(mapInstance);

            const popStyle = getPopupStyle();
            mapMarker.bindPopup(
                `<div style="${popStyle} padding:10px 14px; box-shadow:0 6px 24px rgba(0,0,0,0.2); line-height:1.6">
                   <p style="font-weight:700;font-size:13px;margin:0 0 4px">📦 Package Location</p>
                   <p style="font-size:12px;color:#94a3b8;margin:0">${parseFloat(lat).toFixed(4)}°, ${parseFloat(lng).toFixed(4)}°</p>
                 </div>`,
                { closeButton: false, className: 'pkg-popup' }
            ).openPopup();

            // Coords in footer
            const coordEl = document.getElementById('map-coords');
            if (coordEl) coordEl.textContent = `${parseFloat(lat).toFixed(5)}, ${parseFloat(lng).toFixed(5)}`;
        }, 150);
    }
});
