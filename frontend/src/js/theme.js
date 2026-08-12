/**
 * theme.js — Light/dark mode manager
 * Respects prefers-color-scheme on first visit.
 * Persists user preference in localStorage.
 * Exposes: ThemeManager.toggle(), ThemeManager.current
 */
const ThemeManager = (() => {
    const STORAGE_KEY = 'goexpressly-theme';
    const ROOT = document.documentElement;

    function getSystemPreference() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function getStoredPreference() {
        return localStorage.getItem(STORAGE_KEY);
    }

    function applyTheme(theme) {
        if (theme === 'dark') {
            ROOT.classList.add('dark');
        } else {
            ROOT.classList.remove('dark');
        }
        // Update all toggle buttons
        document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
            btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
            const sunIcon = btn.querySelector('[data-icon="sun"]');
            const moonIcon = btn.querySelector('[data-icon="moon"]');
            if (sunIcon) sunIcon.classList.toggle('hidden', theme !== 'dark');
            if (moonIcon) moonIcon.classList.toggle('hidden', theme === 'dark');
        });
    }

    function init() {
        const stored = getStoredPreference();
        const theme = stored || getSystemPreference();
        applyTheme(theme);

        // System preference change listener (when no stored preference)
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (!getStoredPreference()) {
                applyTheme(e.matches ? 'dark' : 'light');
            }
        });

        // Wire all toggle buttons
        document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
            btn.addEventListener('click', toggle);
        });
    }

    function toggle() {
        const current = ROOT.classList.contains('dark') ? 'dark' : 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem(STORAGE_KEY, next);
        applyTheme(next);
    }

    function current() {
        return ROOT.classList.contains('dark') ? 'dark' : 'light';
    }

    // Run immediately so no flash of wrong theme
    (() => {
        const stored = getStoredPreference();
        const theme = stored || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        if (theme === 'dark') ROOT.classList.add('dark');
    })();

    return { init, toggle, current };
})();

document.addEventListener('DOMContentLoaded', () => ThemeManager.init());

// Global App Preloader dismissal
(() => {
    function hidePreloader() {
        const loader = document.getElementById('app-preloader');
        if (loader && !loader.classList.contains('opacity-0')) {
            loader.classList.add('opacity-0', 'pointer-events-none');
            setTimeout(() => {
                if (loader && loader.parentNode) loader.parentNode.removeChild(loader);
            }, 450);
        }
    }

    if (document.readyState === 'complete') {
        hidePreloader();
    } else {
        window.addEventListener('load', hidePreloader);
        // Fallback max 2 seconds
        setTimeout(hidePreloader, 2000);
    }
})();
