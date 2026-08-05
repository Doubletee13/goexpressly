/**
 * auth.js — Admin login page logic
 */
document.addEventListener('DOMContentLoaded', () => {
    // Redirect if already logged in
    if (Api.isAuthenticated()) window.location.href = 'dashboard.html';

    const form = document.getElementById('login-form');
    const btn = document.getElementById('login-btn');
    const btnText = document.getElementById('login-btn-text');
    const spinner = document.getElementById('login-spinner');
    const errBox = document.getElementById('login-error');
    const errText = document.getElementById('login-error-text');
    const pwInput = document.getElementById('password');
    const pwToggle = document.getElementById('pw-toggle');
    const eyeOpen = document.getElementById('pw-eye-open');
    const eyeClosed = document.getElementById('pw-eye-closed');

    // Password visibility toggle
    pwToggle.addEventListener('click', () => {
        const isPassword = pwInput.type === 'password';
        pwInput.type = isPassword ? 'text' : 'password';
        eyeOpen.classList.toggle('hidden', isPassword);
        eyeClosed.classList.toggle('hidden', !isPassword);
    });

    // Form submit
    form.addEventListener('submit', async e => {
        e.preventDefault();
        const email = document.getElementById('email').value.trim();
        const password = pwInput.value;
        if (!email || !password) return;

        setLoading(true);
        errBox.classList.add('hidden');

        try {
            await Api.login(email, password);
            window.location.href = 'dashboard.html';
        } catch (err) {
            errText.textContent = err.status === 401
                ? 'Invalid email or password. Please try again.'
                : (err.detail || 'Something went wrong. Please try again.');
            errBox.classList.remove('hidden');
            setLoading(false);
        }
    });

    function setLoading(loading) {
        btn.disabled = loading;
        btnText.textContent = loading ? 'Signing in...' : 'Sign In';
        spinner.classList.toggle('hidden', !loading);
    }
});
