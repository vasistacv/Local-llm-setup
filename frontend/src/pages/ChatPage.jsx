import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth, useTheme } from '../context';
import { clearToken, listConversations, deleteConversation, getMessages, streamChat, adminStats, adminUsers, adminDeleteUser, register } from '../utils/api';

// ── Icons ──────────────────────────────────────────────
const Icon = ({ path, size = 15 }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d={path} />
    </svg>
);

const PlusIcon = () => <Icon path="M12 5v14M5 12h14" />;
const ChatIcon = () => <Icon path="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />;
const KeyIcon = () => <Icon path="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4" />;
const AdminIcon = () => <Icon path="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />;
const LogoutIcon = () => <Icon path="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />;
const TrashIcon = () => <Icon path="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" size={13} />;
const SendIcon = () => <Icon path="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" size={16} />;

// ── Markdown renderer ──────────────────────────────────
function MD({ text }) {
    const html = text
        .replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
        .replace(/`([^`\n]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br/>');
    return <span dangerouslySetInnerHTML={{ __html: '<p>' + html + '</p>' }} />;
}

// ── Typing indicator ─────────────────────────────
function TypingDots() {
    return (
        <div className="typing-indicator">
            <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
        </div>
    );
}

// ═══════════════════════════════════════════════════
// MAIN CHAT PAGE
// ═══════════════════════════════════════════════════
export default function ChatPage() {
    const { user, setUser } = useAuth();
    const { theme, toggle } = useTheme();

    const [view, setView] = useState('chat');
    const [conversations, setConvs] = useState([]);
    const [convId, setConvId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [chatTitle, setChatTitle] = useState('New conversation');
    const [input, setInput] = useState('');
    const [busy, setBusy] = useState(false);
    const [streamText, setStreamText] = useState('');

    // Admin state
    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [crUser, setCrUser] = useState({ u: '', e: '', p: '' });
    const [crMsg, setCrMsg] = useState(null);

    const msgsRef = useRef(null);
    const inputRef = useRef(null);

    // Load conversations on mount
    useEffect(() => { loadConvs(); }, []);

    // Scroll to bottom when messages change
    useEffect(() => {
        if (msgsRef.current) msgsRef.current.scrollTop = msgsRef.current.scrollHeight;
    }, [messages, streamText]);

    async function loadConvs() {
        try { const d = await listConversations(); setConvs(d.conversations); } catch { }
    }

    async function loadAdminData() {
        try {
            const [s, u] = await Promise.all([adminStats(), adminUsers()]);
            setStats(s); setUsers(u.users);
        } catch { }
    }

    function logout() {
        clearToken(); setUser(null);
    }

    function newChat() {
        setConvId(null); setMessages([]); setChatTitle('New conversation');
        setView('chat');
    }

    async function openConv(id, title) {
        setConvId(id); setChatTitle(title); setView('chat');
        try {
            const d = await getMessages(id);
            setMessages(d.messages.map(m => ({ role: m.role, text: m.content })));
        } catch { }
    }

    async function delConv(e, id) {
        e.stopPropagation();
        await deleteConversation(id).catch(() => { });
        if (convId === id) newChat();
        loadConvs();
    }

    function handleView(v) {
        setView(v);
        if (v === 'admin') loadAdminData();
    }

    // Auto-resize textarea
    function handleInputChange(e) {
        setInput(e.target.value);
        const el = e.target;
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 180) + 'px';
    }

    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    }

    async function sendMessage(overrideText) {
        const text = (overrideText || input).trim();
        if (!text || busy) return;
        setInput('');
        if (inputRef.current) inputRef.current.style.height = 'auto';

        const userMsg = { role: 'user', text };
        setMessages(prev => [...prev, userMsg]);
        setBusy(true);
        setStreamText('');

        let currentId = convId;
        let full = '';

        try {
            await streamChat(
                text,
                currentId,
                (chunk) => { full += chunk; setStreamText(full); },
                (newId) => { currentId = newId; setConvId(newId); }
            );
            setMessages(prev => [...prev, { role: 'assistant', text: full }]);
            setStreamText('');
            const title = text.slice(0, 48) + (text.length > 48 ? '…' : '');
            setChatTitle(title);
            loadConvs();
        } catch (ex) {
            setMessages(prev => [...prev, { role: 'assistant', text: `Error: ${ex.message}` }]);
            setStreamText('');
        } finally {
            setBusy(false);
        }
    }

    async function createUser() {
        const { u, e, p } = crUser;
        if (!u || !e || !p) { setCrMsg({ type: 'error', text: 'All fields required.' }); return; }
        try {
            const d = await register(u, e, p);
            setCrMsg({ type: 'success', text: `✅ Account created! API Key: ${d.api_key}` });
            setCrUser({ u: '', e: '', p: '' });
            loadAdminData();
        } catch (ex) {
            setCrMsg({ type: 'error', text: ex.message });
        }
        setTimeout(() => setCrMsg(null), 8000);
    }

    async function removeUser(id) {
        if (!confirm('Remove this user? They will lose access immediately.')) return;
        await adminDeleteUser(id).catch(() => { });
        loadAdminData();
    }

    function copyKey() {
        navigator.clipboard.writeText(user?.api_key || '');
        const btn = document.querySelector('.copy-btn');
        if (btn) { const t = btn.textContent; btn.textContent = 'Copied!'; setTimeout(() => btn.textContent = t, 2000); }
    }

    const suggestions = [
        { icon: '🐍', text: 'Write a binary search tree in Python' },
        { icon: '🧮', text: 'Explain gradient descent intuitively' },
        { icon: '🗄️', text: 'Optimize a SQL query with millions of rows' },
        { icon: '⚛️', text: 'React hooks best practices and patterns' },
    ];

    return (
        <div className="app-layout">
            {/* ══ SIDEBAR ══ */}
            <aside className="sidebar">
                <div className="sb-header">
                    <div className="sb-brand-row">
                        <div className="sb-logo">
                            <div className="sb-logo-mark">✦</div>
                            <span className="sb-logo-name">JITD AI</span>
                        </div>
                        <button className="theme-toggle" onClick={toggle} title="Toggle theme">
                            {theme === 'dark' ? '☀️' : '🌙'}
                        </button>
                    </div>
                    <button className="new-chat-btn" onClick={newChat}>
                        <PlusIcon />&nbsp; New conversation
                    </button>
                </div>

                {/* History */}
                <div className="sb-history">
                    {conversations.length === 0 ? (
                        <div className="empty-state">No conversations yet</div>
                    ) : (
                        <>
                            <div className="sb-section-label">Recent</div>
                            {conversations.map(c => (
                                <div
                                    key={c.id}
                                    className={`conv-item ${c.id === convId ? 'active' : ''}`}
                                    onClick={() => openConv(c.id, c.title)}
                                >
                                    <span className="conv-title">{c.title}</span>
                                    <button className="conv-del" onClick={e => delConv(e, c.id)}><TrashIcon /></button>
                                </div>
                            ))}
                        </>
                    )}
                </div>

                <div className="sb-divider" />

                {/* Nav */}
                <div className="sb-nav">
                    <button className={`sb-nav-item ${view === 'apikey' ? 'active' : ''}`} onClick={() => setView('apikey')}>
                        <KeyIcon /> My API Key
                    </button>
                    {user?.role === 'admin' && (
                        <button className={`sb-nav-item ${view === 'admin' ? 'active' : ''}`} onClick={() => handleView('admin')}>
                            <AdminIcon /> Admin Panel
                        </button>
                    )}
                </div>

                {/* User */}
                <div className="sb-footer">
                    <div className="user-card">
                        <div className="user-avatar">{user?.username?.[0]?.toUpperCase()}</div>
                        <div className="user-details">
                            <div className="user-name">{user?.username}</div>
                            <div className="user-role">{user?.role}</div>
                        </div>
                        <button className="logout-btn" onClick={logout} title="Sign out">
                            <LogoutIcon />
                        </button>
                    </div>
                </div>
            </aside>

            {/* ══ MAIN ══ */}
            <div className="main-content">

                {/* ─ CHAT VIEW ─ */}
                {view === 'chat' && (
                    <>
                        <div className="topbar">
                            <div>
                                <div className="tb-title">{chatTitle}</div>
                            </div>
                            <span className="model-badge">Auto-routing · 14B Models</span>
                        </div>

                        <div className="messages-area" ref={msgsRef}>
                            {messages.length === 0 && !busy ? (
                                <div className="welcome-screen">
                                    <div className="welcome-icon">✦</div>
                                    <h2>How can I help you today?</h2>
                                    <p>Ask anything — code, analysis, science, writing, research. I'll route your question to the best model automatically.</p>
                                    <div className="suggestion-grid">
                                        {suggestions.map(s => (
                                            <button key={s.text} className="suggestion-card" onClick={() => sendMessage(s.text)}>
                                                <span className="card-icon">{s.icon}</span>
                                                {s.text}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <>
                                    {messages.map((m, i) => (
                                        <div key={i} className={`message-row ${m.role === 'user' ? 'user' : 'ai'}`}>
                                            <div className={`msg-avatar ${m.role === 'user' ? 'user' : 'ai'}`}>
                                                {m.role === 'user' ? user?.username?.[0]?.toUpperCase() : '✦'}
                                            </div>
                                            <div className="msg-body">
                                                <div className="msg-bubble">
                                                    {m.role === 'assistant' ? <MD text={m.text} /> : m.text}
                                                </div>
                                            </div>
                                        </div>
                                    ))}

                                    {/* Streaming */}
                                    {busy && (
                                        <div className="message-row ai">
                                            <div className="msg-avatar ai">✦</div>
                                            <div className="msg-body">
                                                <div className="msg-bubble">
                                                    {streamText ? <MD text={streamText} /> : <TypingDots />}
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>

                        <div className="input-area">
                            <div className="input-container">
                                <textarea
                                    ref={inputRef}
                                    className="chat-input"
                                    placeholder="Message JITD AI…"
                                    value={input}
                                    onChange={handleInputChange}
                                    onKeyDown={handleKeyDown}
                                    rows={1}
                                />
                                <button className="send-btn" onClick={() => sendMessage()} disabled={busy || !input.trim()}>
                                    <SendIcon />
                                </button>
                            </div>
                            <div className="input-hint">JITD AI can make mistakes. Always verify important information.</div>
                        </div>
                    </>
                )}

                {/* ─ API KEY VIEW ─ */}
                {view === 'apikey' && (
                    <>
                        <div className="topbar">
                            <div><div className="tb-title">My API Key</div><div className="tb-sub">Use this key for programmatic API access</div></div>
                        </div>
                        <div className="page-view">
                            <div className="apikey-panel">
                                <div className="key-label">Personal API Key</div>
                                <div className="key-box">
                                    <span className="key-val">{user?.api_key}</span>
                                    <button className="copy-btn" onClick={copyKey}>Copy</button>
                                </div>
                                <h4 style={{ fontSize: 13, fontWeight: 600, marginBottom: 10, color: 'var(--text2)' }}>Usage example</h4>
                                <div className="code-block">{`curl -X POST https://your-tunnel.trycloudflare.com/chat \\
  -H "x-api-key: ${user?.api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hello JITD AI!"}'`}</div>
                            </div>
                        </div>
                    </>
                )}

                {/* ─ ADMIN VIEW ─ */}
                {view === 'admin' && user?.role === 'admin' && (
                    <>
                        <div className="topbar">
                            <div><div className="tb-title">Admin Panel</div><div className="tb-sub">Manage users and monitor platform activity</div></div>
                            <button className="btn-primary" onClick={loadAdminData}>↻ Refresh</button>
                        </div>
                        <div className="page-view">
                            {/* Stats */}
                            <div className="stats-grid">
                                {[
                                    { icon: '👥', v: stats?.total_users ?? '—', l: 'Total users' },
                                    { icon: '🎓', v: stats?.students ?? '—', l: 'Students' },
                                    { icon: '💬', v: stats?.total_calls ?? '—', l: 'Total queries' },
                                    { icon: '🤖', v: 2, l: 'Active models' },
                                ].map(s => (
                                    <div className="stat-card" key={s.l}>
                                        <div className="stat-icon">{s.icon}</div>
                                        <div className="stat-value">{s.v}</div>
                                        <div className="stat-label">{s.l}</div>
                                    </div>
                                ))}
                            </div>

                            {/* Create user */}
                            <div className="panel">
                                <div className="panel-header"><h3>Create Student Account</h3></div>
                                <div className="panel-body">
                                    <div className="create-form">
                                        <input placeholder="Username" value={crUser.u} onChange={e => setCrUser(p => ({ ...p, u: e.target.value }))} />
                                        <input placeholder="Email address" type="email" value={crUser.e} onChange={e => setCrUser(p => ({ ...p, e: e.target.value }))} />
                                        <input placeholder="Password" type="password" value={crUser.p} onChange={e => setCrUser(p => ({ ...p, p: e.target.value }))} />
                                        <button className="btn-primary" onClick={createUser}>Create</button>
                                    </div>
                                    {crMsg && <div className={`feedback ${crMsg.type}`}>{crMsg.text}</div>}
                                </div>
                            </div>

                            {/* Users table */}
                            <div className="panel">
                                <div className="panel-header"><h3>All Users</h3><span style={{ fontSize: 12, color: 'var(--text3)' }}>{users.length} total</span></div>
                                <div className="panel-body no-pad">
                                    <div className="table-wrapper">
                                        <table>
                                            <thead>
                                                <tr><th>User</th><th>Email</th><th>Role</th><th>API Key</th><th>Queries</th><th>Status</th><th>Joined</th><th></th></tr>
                                            </thead>
                                            <tbody>
                                                {users.map(u => (
                                                    <tr key={u.id}>
                                                        <td><strong>{u.username}</strong></td>
                                                        <td style={{ color: 'var(--text3)' }}>{u.email}</td>
                                                        <td><span className={`badge badge-${u.role}`}>{u.role}</span></td>
                                                        <td><span className="mono">{u.api_key?.slice(0, 20)}…</span></td>
                                                        <td>{u.total_calls}</td>
                                                        <td><span className={`badge badge-${u.is_active ? 'active' : 'inactive'}`}>{u.is_active ? 'Active' : 'Removed'}</span></td>
                                                        <td style={{ color: 'var(--text3)' }}>{new Date(u.created_at).toLocaleDateString()}</td>
                                                        <td>{u.role !== 'admin' && <button className="btn-danger" onClick={() => removeUser(u.id)}>Remove</button>}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
