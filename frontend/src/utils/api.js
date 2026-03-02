// Central API utility — all fetch calls go through here
const BASE = '';

export function getToken() {
    return localStorage.getItem('jitd_token');
}

export function setToken(t) {
    localStorage.setItem('jitd_token', t);
}

export function clearToken() {
    localStorage.removeItem('jitd_token');
}

function authHeaders(extra = {}) {
    const token = getToken();
    return {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...extra,
    };
}

async function call(path, opts = {}) {
    const res = await fetch(BASE + path, {
        headers: authHeaders(),
        ...opts,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
}

// Auth
export const register = (username, email, password) =>
    call('/auth/register', { method: 'POST', body: JSON.stringify({ username, email, password }) });

export const login = (username, password) =>
    call('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });

export const fetchMe = () => call('/auth/me');

// Conversations
export const listConversations = () => call('/conversations');
export const newConversation = () => call('/conversations', { method: 'POST' });
export const getMessages = (id) => call(`/conversations/${id}/messages`);
export const deleteConversation = (id) => call(`/conversations/${id}`, { method: 'DELETE' });

// Admin
export const adminStats = () => call('/api/admin/stats');
export const adminUsers = () => call('/api/admin/users');
export const adminDeleteUser = (id) => call(`/api/admin/users/${id}`, { method: 'DELETE' });

// Streaming chat
export async function streamChat(message, conversationId, onChunk, onConvId) {
    const token = getToken();
    const res = await fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message, conversation_id: conversationId }),
    });

    if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error(e.detail || 'Chat failed');
    }

    // Pass conversation ID back
    const cid = parseInt(res.headers.get('X-Conversation-Id'));
    if (cid && onConvId) onConvId(cid);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        onChunk(decoder.decode(value, { stream: true }));
    }
}
