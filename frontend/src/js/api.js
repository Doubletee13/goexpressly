/**
 * api.js — Fetch wrapper for GoExpressly API
 * Backend is proxied through /api (same origin in production).
 * In dev, the Vite/nginx proxy or direct localhost:8000 is used.
 */
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://goexpressly.onrender.com';  // Render backend

const Api = {
    _getToken() {
        return localStorage.getItem('gx_token');
    },

    _headers(extra = {}) {
        const token = this._getToken();
        return {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...extra,
        };
    },

    async _request(method, path, body = null, formData = false) {
        const opts = {
            method,
            headers: formData ? {} : this._headers(),
        };
        if (body && formData) {
            // For OAuth2 form submission
            const token = this._getToken();
            if (token) opts.headers.Authorization = `Bearer ${token}`;
            opts.body = body;
        } else if (body) {
            opts.body = JSON.stringify(body);
        }
        const res = await fetch(`${API_BASE}${path}`, opts);
        if (res.status === 204) return null;
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw { status: res.status, detail: data.detail || 'An error occurred' };
        return data;
    },

    // ── Auth ──────────────────────────────────────────────────────────────
    async login(email, password) {
        const form = new URLSearchParams();
        form.append('username', email);
        form.append('password', password);
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: form.toString(),
        });
        const data = await res.json();
        if (!res.ok) throw { status: res.status, detail: data.detail || 'Login failed' };
        localStorage.setItem('gx_token', data.access_token);
        return data;
    },

    async getMe() {
        return this._request('GET', '/api/auth/me');
    },

    logout() {
        localStorage.removeItem('gx_token');
        window.location.href = '/login';
    },

    isAuthenticated() {
        return !!this._getToken();
    },

    // ── Public Tracking ───────────────────────────────────────────────────
    async trackPackage(trackingId) {
        return this._request('GET', `/api/track/${encodeURIComponent(trackingId)}`);
    },

    // ── Contact Form ──────────────────────────────────────────────────────
    async submitContactForm(data) {
        return this._request('POST', '/api/contact', data);
    },

    // ── Packages (Admin) ──────────────────────────────────────────────────
    async listPackages(page = 1, pageSize = 20) {
        return this._request('GET', `/api/packages?page=${page}&page_size=${pageSize}`);
    },

    async createPackage(data) {
        return this._request('POST', '/api/packages', data);
    },

    async getPackage(id) {
        return this._request('GET', `/api/packages/${id}`);
    },

    async updatePackage(id, data) {
        return this._request('PATCH', `/api/packages/${id}`, data);
    },

    async deletePackage(id) {
        return this._request('DELETE', `/api/packages/${id}`);
    },

    // ── Tracking Events (Admin) ───────────────────────────────────────────
    async addEvent(packageId, data) {
        return this._request('POST', `/api/packages/${packageId}/events`, data);
    },

    async listEvents(packageId) {
        return this._request('GET', `/api/packages/${packageId}/events`);
    },
};
