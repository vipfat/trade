/**
 * Trading Bot Control Panel - Main JavaScript
 * Основной JavaScript файл для управления ботом
 */

// Проверка аутентификации при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    checkAuthentication();
    setupLoginForm();
});

// Проверка статуса аутентификации
async function checkAuthentication() {
    try {
        const response = await fetch('/api/is-authenticated');
        const data = await response.json();
        
        if (!data.authenticated) {
            showLoginForm();
        } else {
            showMainContent();
        }
    } catch (error) {
        console.error('Auth check error:', error);
    }
}

// Отображение формы входа
function showLoginForm() {
    const body = document.body;
    body.innerHTML = `
        <div style="min-height: 100vh; display: flex; justify-content: center; align-items: center;">
            <div class="card" style="width: 100%; max-width: 400px;">
                <div class="card-header">
                    <h4><i class="bi bi-lock"></i> Trading Bot Control Panel</h4>
                </div>
                <div class="card-body">
                    <form id="loginForm">
                        <div class="mb-3">
                            <label class="form-label">Имя пользователя</label>
                            <input type="text" id="username" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Пароль</label>
                            <input type="password" id="password" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Войти</button>
                    </form>
                </div>
            </div>
        </div>
    `;
}

// Отображение основного контента
function showMainContent() {
    // Основной контент уже есть в HTML
}

// Настройка формы входа
function setupLoginForm() {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) return;
    
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Неверные учетные данные');
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('Ошибка входа');
        }
    });
}

// Функция выхода
function logout() {
    fetch('/api/logout', { method: 'POST' })
        .then(() => window.location.href = '/')
        .catch(err => console.error('Logout error:', err));
}

// Отображение уведомления
function showNotification(message, type = 'info') {
    const alertClass = `alert alert-${type}`;
    const notification = `
        <div class="${alertClass}" role="alert" style="position: fixed; top: 20px; right: 20px; max-width: 400px; z-index: 9999;">
            <i class="bi bi-exclamation-circle"></i> ${message}
        </div>
    `;
    
    const alert = document.createElement('div');
    alert.innerHTML = notification;
    document.body.appendChild(alert);
    
    setTimeout(() => alert.remove(), 5000);
}

// Форматирование чисел
function formatNumber(num) {
    return new Intl.NumberFormat('ru-RU').format(num);
}

// Форматирование байтов
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Форматирование времени
function formatTime(date) {
    return new Intl.DateTimeFormat('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }).format(new Date(date));
}

// Экранирование HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Копирование в буфер обмена
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Скопировано в буфер обмена', 'success');
    }).catch(err => {
        console.error('Copy error:', error);
        showNotification('Ошибка копирования', 'danger');
    });
}

// Загрузка содержимого файла
async function loadFileContent(filename) {
    try {
        const response = await fetch(`/api/files/${filename}`);
        const content = await response.text();
        return content;
    } catch (error) {
        console.error('Error loading file:', error);
        return null;
    }
}

// Запросить подтверждение
function confirm(message) {
    return window.confirm(message);
}

// Запросить ввод
function prompt(message, defaultValue = '') {
    return window.prompt(message, defaultValue);
}

// API Request Helper
async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };
    
    try {
        const response = await fetch(endpoint, mergedOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API request error for ${endpoint}:`, error);
        throw error;
    }
}

// Storage Helper
const Storage = {
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Storage set error:', error);
        }
    },
    
    get: (key, defaultValue = null) => {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : defaultValue;
        } catch (error) {
            console.error('Storage get error:', error);
            return defaultValue;
        }
    },
    
    remove: (key) => {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Storage remove error:', error);
        }
    },
    
    clear: () => {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('Storage clear error:', error);
        }
    }
};

// Debounce функция
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// Throttle функция
function throttle(func, delay) {
    let lastCall = 0;
    return function (...args) {
        const now = Date.now();
        if (now - lastCall >= delay) {
            func.apply(this, args);
            lastCall = now;
        }
    };
}

// Отправка POST запроса с JSON
async function postJSON(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    } catch (error) {
        console.error('POST error:', error);
        throw error;
    }
}

// Отправка GET запроса
async function getJSON(url) {
    try {
        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.error('GET error:', error);
        throw error;
    }
}

// Экспорт функций для использования в шаблонах
window.showNotification = showNotification;
window.formatNumber = formatNumber;
window.formatBytes = formatBytes;
window.formatTime = formatTime;
window.escapeHtml = escapeHtml;
window.copyToClipboard = copyToClipboard;
window.apiRequest = apiRequest;
window.Storage = Storage;
window.postJSON = postJSON;
window.getJSON = getJSON;
window.logout = logout;

// Обработчик ошибок в консоли
window.addEventListener('error', (event) => {
    console.error('Unhandled error:', event.error);
});

// Обработчик необработанных promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});
