// Configuration
const API_URL = `${window.location.origin}/api/v1/chat/stream`;
const SESSION_STORAGE_KEY = 'hr_chatbot_session_id';
const CREDENTIALS_KEY = 'hr_chatbot_credentials';

// State
let currentSessionId = getStoredSessionId();
let isStreaming = false;
let currentController = null;

// DOM Elements
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const stopBtn = document.getElementById('stopBtn');
const chatMessages = document.getElementById('chatMessages');
const typingIndicator = document.getElementById('typingIndicator');
const themeToggle = document.getElementById('themeToggle');
const themeLabel = document.getElementById('themeLabel');
const menuToggle = document.getElementById('menuToggle');
const sidebar = document.getElementById('sidebar');
const newChatBtn = document.getElementById('newChatBtn');
const logoutBtn = document.getElementById('logoutBtn');
const quickQuestions = document.getElementById('quickQuestions');

// Credentials Management
function getCredentials() {
    return localStorage.getItem(CREDENTIALS_KEY);
}

function clearCredentials() {
    localStorage.removeItem(CREDENTIALS_KEY);
}

function handleLogout() {
    clearCredentials();
    window.location.href = 'login.html';
}

// Session Management
function getStoredSessionId() {
    const savedSessionId = localStorage.getItem(SESSION_STORAGE_KEY);

    if (savedSessionId) {
        return savedSessionId;
    }

    const newSessionId = createSessionId();
    localStorage.setItem(SESSION_STORAGE_KEY, newSessionId);
    return newSessionId;
}

function createSessionId() {
    if (crypto.randomUUID) {
        return crypto.randomUUID();
    }

    return `session_${Date.now()}`;
}

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeLabel(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeLabel(newTheme);
}

function updateThemeLabel(theme) {
    themeLabel.textContent = theme === 'dark' ? 'Chế độ sáng' : 'Chế độ tối';
}

// Chat Management
function createNewChat() {
    currentSessionId = createSessionId();
    localStorage.setItem(SESSION_STORAGE_KEY, currentSessionId);
    chatMessages.innerHTML = '';
    addMessage('assistant', 'Xin chào! Tôi là Trợ lý Nhân sự của công ty. Tôi có thể giúp gì cho bạn?');
    if (quickQuestions) {
        quickQuestions.classList.remove('hidden');
    }
}

function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (role === 'assistant') {
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    scrollToBottom();
}

function addStreamingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant streaming';
    messageDiv.style.display = 'none';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    return { messageDiv, contentDiv };
}

function updateStreamingMessage(contentDiv, chunk) {
    contentDiv.textContent += chunk;
}

function finalizeStreamingMessage(messageDiv, contentDiv, fullContent) {
    contentDiv.innerHTML = marked.parse(fullContent);
    messageDiv.style.display = '';
    scrollToBottom();
}

function scrollToBottom() {
    const wrapper = chatMessages.parentElement;
    wrapper.scrollTop = wrapper.scrollHeight;
}

// API Communication
async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message || isStreaming) return;

    addMessage('user', message);
    messageInput.value = '';
    messageInput.style.height = 'auto';
    sendBtn.disabled = true;
    hideQuickQuestions();

    isStreaming = true;
    typingIndicator.style.display = 'block';
    stopBtn.style.display = 'flex';

    try {
        const { messageDiv: streamingDiv, contentDiv: streamingContent } = addStreamingMessage();
        let fullResponse = '';

        currentController = new AbortController();

        const credentials = getCredentials();
        if (!credentials) {
            window.location.href = 'login.html';
            return;
        }

        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Basic ${credentials}`,
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId,
            }),
            signal: currentController.signal,
        });

        if (response.status === 401) {
            handleLogout();
            return;
        }

        if (!response.ok) {
            throw new Error('Không thể kết nối đến máy chủ');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            const chunk = decoder.decode(value);
            fullResponse += chunk;
            updateStreamingMessage(streamingContent, chunk);
        }

        finalizeStreamingMessage(streamingDiv, streamingContent, fullResponse);
    } catch (error) {
        if (error.name === 'AbortError') {
            if (streamingDiv) {
                streamingDiv.remove();
            }
        } else {
            addMessage('assistant', 'Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi của bạn. Vui lòng thử lại.');
        }
    } finally {
        isStreaming = false;
        currentController = null;
        typingIndicator.style.display = 'none';
        stopBtn.style.display = 'none';
        sendBtn.disabled = !messageInput.value.trim();
    }
}

function stopStreaming() {
    if (currentController) {
        currentController.abort();
    }
}

// Event Listeners
messageInput.addEventListener('input', () => {
    sendBtn.disabled = !messageInput.value.trim();
    autoResizeTextarea();
});

messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener('click', sendMessage);
stopBtn.addEventListener('click', stopStreaming);
themeToggle.addEventListener('click', toggleTheme);
newChatBtn.addEventListener('click', createNewChat);
logoutBtn.addEventListener('click', handleLogout);

menuToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');

    let overlay = document.querySelector('.sidebar-overlay');
    if (sidebar.classList.contains('open')) {
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            overlay.addEventListener('click', () => {
                sidebar.classList.remove('open');
                overlay.remove();
            });
            document.body.appendChild(overlay);
        }
    } else if (overlay) {
        overlay.remove();
    }
});

// Utility Functions
function autoResizeTextarea() {
    messageInput.style.height = 'auto';
    messageInput.style.height = `${Math.min(messageInput.scrollHeight, 120)}px`;
}

function hideQuickQuestions() {
    if (quickQuestions) {
        quickQuestions.classList.add('hidden');
    }
}

// Quick Questions
document.querySelectorAll('.quick-question-card').forEach(card => {
    card.addEventListener('click', () => {
        const question = card.getAttribute('data-question');
        messageInput.value = question;
        sendBtn.disabled = false;
        autoResizeTextarea();
        sendMessage();
    });
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!getCredentials()) {
        window.location.href = 'login.html';
        return;
    }

    initTheme();
    messageInput.focus();
});
