/* ═══════════════════════════════════════════════════════════
   COLLEGE AI ENTERPRISE — Full JavaScript
   Auth, Chat, Admin Panel, API Key management
═══════════════════════════════════════════════════════════ */

let currentUser = null;
let sessionToken = null;
let isGenerating = false;

// ── Init ─────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
    const savedToken = localStorage.getItem('college_token');
    if (savedToken) {
        sessionToken = savedToken;
        const user = await fetchMe();
        if (user) {
            loginSuccess(user);
            return;
        }
        localStorage.removeItem('college_token');
    }
    showAuthScreen();
});

// ── Auth Screen ───────────────────────────────────────────
function showAuthScreen() {
    document.getElementById('auth-screen').style.display = 'flex';
    document.getElementById('app').style.display = 'none';
}

function showApp() {
    document.getElementById('auth-screen').style.display = 'none';
    document.getElementById('app').style.display = 'flex';
}

function switchTab(tab) {
    document.getElementById('tab-login').classList.toggle('active', tab === 'login');
    document.getElementById('tab-register').classList.toggle('active', tab === 'register');
    document.getElementById('login-form').style.display = tab === 'login' ? 'flex' : 'none';
    document.getElementById('register-form').style.display = tab === 'register' ? 'flex' : 'none';
    document.getElementById('login-error').textContent = '';
    document.getElementById('register-error').textContent = '';
}

// ── Login ─────────────────────────────────────────────────
async function handleLogin(event) {
    event.preventDefault();
    const btn = document.getElementById('login-btn');
    setLoading(btn, true);

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    try {
        const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Login failed');

        sessionToken = data.token;
        localStorage.setItem('college_token', sessionToken);
        loginSuccess(data.user);
    } catch (e) {
        document.getElementById('login-error').textContent = e.message;
    } finally {
        setLoading(btn, false);
    }
}

// ── Register ──────────────────────────────────────────────
async function handleRegister(event) {
    event.preventDefault();
    const btn = document.getElementById('register-btn');
    setLoading(btn, true);

    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;

    try {
        const res = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Registration failed');

        // Auto login after register
        await document.getElementById('login-username').setAttribute('value', username);
        const loginRes = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const loginData = await loginRes.json();
        sessionToken = loginData.token;
        localStorage.setItem('college_token', sessionToken);
        loginSuccess(loginData.user);
    } catch (e) {
        document.getElementById('register-error').textContent = e.message;
    } finally {
        setLoading(btn, false);
    }
}

// ── Post Login Setup ──────────────────────────────────────
function loginSuccess(user) {
    currentUser = user;
    document.getElementById('user-name').textContent = user.username;
    document.getElementById('user-role').textContent = user.role;
    document.getElementById('user-avatar').textContent = user.username[0].toUpperCase();
    document.getElementById('my-api-key').textContent = user.api_key;

    // Show admin nav if admin
    if (user.role === 'admin') {
        document.getElementById('nav-admin').style.display = 'flex';
        loadAdminData();
    }

    showApp();
    showView('chat');
}

async function fetchMe() {
    try {
        const res = await fetch('/auth/me', {
            headers: { 'Authorization': `Bearer ${sessionToken}` }
        });
        if (!res.ok) return null;
        return await res.json();
    } catch { return null; }
}

function logout() {
    localStorage.removeItem('college_token');
    sessionToken = null;
    currentUser = null;
    showAuthScreen();
}

// ── Navigation ────────────────────────────────────────────
function showView(name) {
    ['chat', 'admin', 'apikey'].forEach(v => {
        document.getElementById('view-' + v).classList.toggle('active', v === name);
        const navBtn = document.getElementById('nav-' + v);
        if (navBtn) navBtn.classList.toggle('active', v === name);
    });
    if (name === 'admin') loadAdminData();
}

// ── CHAT ──────────────────────────────────────────────────
function quickPrompt(text) {
    document.getElementById('user-input').value = text;
    sendMessage();
}

function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
}

async function sendMessage() {
    if (isGenerating) return;
    const input = document.getElementById('user-input');
    const text = input.value.trim();
    if (!text) return;

    // Clear welcome msg
    const welcome = document.querySelector('.welcome-msg');
    if (welcome) welcome.remove();

    addMessage('user', text);
    input.value = '';
    input.style.height = 'auto';

    const botId = 'bot-' + Date.now();
    addMessage('bot', '', botId);
    isGenerating = true;
    document.getElementById('send-btn').disabled = true;

    const botBubble = document.getElementById(botId);
    botBubble.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${sessionToken}`
            },
            body: JSON.stringify({ message: text })
        });

        if (!response.ok) {
            const err = await response.json();
            botBubble.innerHTML = `<span style="color:#ef4444">Error: ${err.detail || 'Unknown error'}</span>`;
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let full = '';
        botBubble.innerHTML = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            full += decoder.decode(value, { stream: true });
            botBubble.innerHTML = renderMarkdown(full);
            scrollToBottom();
        }
    } catch (e) {
        botBubble.innerHTML = `<span style="color:#ef4444">Connection error: ${e.message}</span>`;
    } finally {
        isGenerating = false;
        document.getElementById('send-btn').disabled = false;
        scrollToBottom();
    }
}

function addMessage(role, text, id = null) {
    const msgs = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = `msg ${role}`;

    const avatar = role === 'user'
        ? (currentUser?.username?.[0]?.toUpperCase() || 'U')
        : '⚡';

    div.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-body">
      <div class="msg-bubble" ${id ? `id="${id}"` : ''}>${text ? renderMarkdown(text) : ''}</div>
    </div>`;
    msgs.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    const msgs = document.getElementById('messages');
    msgs.scrollTop = msgs.scrollHeight;
}

function renderMarkdown(text) {
    return text
        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>');
}

// ── ADMIN ─────────────────────────────────────────────────
async function loadAdminData() {
    try {
        const headers = { 'Authorization': `Bearer ${sessionToken}` };

        const [statsRes, usersRes] = await Promise.all([
            fetch('/api/admin/stats', { headers }),
            fetch('/api/admin/users', { headers })
        ]);

        const stats = await statsRes.json();
        document.getElementById('stat-total').textContent = stats.total_users ?? '—';
        document.getElementById('stat-students').textContent = stats.students ?? '—';
        document.getElementById('stat-calls').textContent = stats.total_calls ?? '—';

        const { users } = await usersRes.json();
        renderUsersTable(users);
    } catch (e) {
        console.error('Admin data error:', e);
    }
}

function renderUsersTable(users) {
    const tbody = document.getElementById('users-tbody');
    tbody.innerHTML = users.map(u => `
    <tr>
      <td><strong>${u.username}</strong></td>
      <td>${u.email}</td>
      <td><span class="role-badge ${u.role}">${u.role}</span></td>
      <td><code class="key-code">${u.api_key.substring(0, 20)}...</code></td>
      <td>${u.total_calls}</td>
      <td>${new Date(u.created_at).toLocaleDateString()}</td>
      <td>${u.role !== 'admin'
            ? `<button class="del-btn" onclick="deactivateUser(${u.id})">Remove</button>`
            : '—'}</td>
    </tr>`).join('');
}

async function createStudent() {
    const username = document.getElementById('new-username').value.trim();
    const email = document.getElementById('new-email').value.trim();
    const password = document.getElementById('new-password').value;

    if (!username || !email || !password) {
        document.getElementById('create-result').innerHTML = '<span style="color:#ef4444">Fill all fields.</span>';
        return;
    }

    try {
        const res = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail);

        document.getElementById('create-result').innerHTML = `
      <div style="color:#10b981;margin-top:10px;padding:12px;background:rgba(16,185,129,0.1);border-radius:8px;">
        ✅ Account created for <strong>${username}</strong><br>
        API Key: <code style="font-size:12px">${data.api_key}</code>
      </div>`;
        document.getElementById('new-username').value = '';
        document.getElementById('new-email').value = '';
        document.getElementById('new-password').value = '';
        loadAdminData();
    } catch (e) {
        document.getElementById('create-result').innerHTML = `<span style="color:#ef4444">Error: ${e.message}</span>`;
    }
}

async function deactivateUser(userId) {
    if (!confirm('Remove this user?')) return;
    await fetch(`/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${sessionToken}` }
    });
    loadAdminData();
}

// ── API KEY ───────────────────────────────────────────────
function copyKey() {
    const key = document.getElementById('my-api-key').textContent;
    navigator.clipboard.writeText(key).then(() => {
        const btn = document.querySelector('.copy-btn');
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = 'Copy', 2000);
    });
}

// ── Utility ───────────────────────────────────────────────
function setLoading(btn, loading) {
    btn.querySelector('.btn-text').style.display = loading ? 'none' : 'inline';
    btn.querySelector('.btn-loader').style.display = loading ? 'inline' : 'none';
    btn.disabled = loading;
}
