// Configuration
const API_URL = `${window.location.origin}/api/v1/auth/verify`;
const CREDENTIALS_KEY = 'hr_chatbot_credentials';

// DOM Elements
const loginForm = document.getElementById('loginForm');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const loginBtn = document.getElementById('loginBtn');
const btnText = loginBtn.querySelector('.btn-text');
const btnLoader = loginBtn.querySelector('.btn-loader');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    // Add theme toggle button
    const themeToggle = document.createElement('button');
    themeToggle.className = 'theme-toggle';
    themeToggle.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
        </svg>
    `;
    themeToggle.addEventListener('click', toggleTheme);
    document.body.appendChild(themeToggle);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Form Validation
function validateForm() {
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();

    if (!username) {
        showError('Vui lòng nhập tên đăng nhập');
        usernameInput.classList.add('error');
        return false;
    }

    if (!password) {
        showError('Vui lòng nhập mật khẩu');
        passwordInput.classList.add('error');
        return false;
    }

    clearErrors();
    return true;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    successMessage.style.display = 'none';

    // Auto-hide error after 5 seconds
    setTimeout(() => {
        if (errorMessage.textContent === message) {
            errorMessage.style.display = 'none';
        }
    }, 5000);
}

function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.style.display = 'block';
    errorMessage.style.display = 'none';
}

function clearErrors() {
    errorMessage.style.display = 'none';
    successMessage.style.display = 'none';
    usernameInput.classList.remove('error');
    passwordInput.classList.remove('error');
}

// Login Logic
async function handleLogin(event) {
    event.preventDefault();

    if (!validateForm()) {
        return;
    }

    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();

    // Set loading state
    setLoading(true);

    try {
        // Test credentials by calling health endpoint with Basic Auth
        const credentials = btoa(`${username}:${password}`);

        const response = await fetch(API_URL, {
            method: 'GET',
            headers: {
                'Authorization': `Basic ${credentials}`
            }
        });

        if (response.ok) {
            // Login successful
            saveCredentials(username, password);
            showSuccess('Đăng nhập thành công! Đang chuyển...');

            // Redirect to chat page after 1 second
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
        } else if (response.status === 401) {
            showError('Tên đăng nhập hoặc mật khẩu không đúng');
            passwordInput.classList.add('error');
        } else {
            showError('Không thể kết nối đến máy chủ');
        }
    } catch (error) {
        showError('Không thể kết nối đến máy chủ');
    } finally {
        setLoading(false);
    }
}

function setLoading(loading) {
    loginBtn.disabled = loading;
    if (loading) {
        btnText.style.display = 'none';
        btnLoader.style.display = 'block';
    } else {
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
    }
}

function saveCredentials(username, password) {
    localStorage.setItem(CREDENTIALS_KEY, btoa(`${username}:${password}`));
}

// Event Listeners
loginForm.addEventListener('submit', handleLogin);

usernameInput.addEventListener('input', () => {
    if (usernameInput.classList.contains('error')) {
        usernameInput.classList.remove('error');
    }
});

passwordInput.addEventListener('input', () => {
    if (passwordInput.classList.contains('error')) {
        passwordInput.classList.remove('error');
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();

    // Check if already logged in
    const credentials = localStorage.getItem(CREDENTIALS_KEY);
    if (credentials) {
        // Redirect to chat page
        window.location.href = 'index.html';
    }

    usernameInput.focus();
});