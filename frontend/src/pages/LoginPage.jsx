import React, { useState } from 'react';
import { useAuth, useTheme } from '../context';
import { login, register, setToken, fetchMe } from '../utils/api';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

export default function LoginPage() {
    const { setUser, setReady } = useAuth();
    const { theme, toggle } = useTheme();

    const [tab, setTab] = useState('login');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Login form state
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    // Register form state
    const [rUser, setRUser] = useState('');
    const [rEmail, setREmail] = useState('');
    const [rPass, setRPass] = useState('');

    async function handleLogin(e) {
        e.preventDefault();
        setError(''); setLoading(true);
        try {
            const data = await login(username, password);
            setToken(data.token);
            const me = await fetchMe();
            setUser(me);
        } catch (ex) {
            setError(ex.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleRegister(e) {
        e.preventDefault();
        setError(''); setLoading(true);
        try {
            await register(rUser, rEmail, rPass);
            const data = await login(rUser, rPass);
            setToken(data.token);
            const me = await fetchMe();
            setUser(me);
        } catch (ex) {
            setError(ex.message);
        } finally {
            setLoading(false);
        }
    }

    function handleGoogle() {
        if (!GOOGLE_CLIENT_ID) {
            setError('Google Sign-In is not configured. Please use username & password.');
            return;
        }
        // Redirect to Google OAuth
        const params = new URLSearchParams({
            client_id: GOOGLE_CLIENT_ID,
            redirect_uri: `${window.location.origin}/auth/google/callback`,
            response_type: 'code',
            scope: 'openid email profile',
            prompt: 'select_account',
        });
        window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params}`;
    }

    return (
        <div className="login-page">
            {/* ── LEFT PANEL ── */}
            <div className="login-left">
                <div className="ll-brand">
                    <div className="ll-logo">✦</div>
                    <span className="ll-name">JITD AI</span>
                    <button
                        onClick={toggle}
                        className="theme-toggle"
                        style={{ marginLeft: 'auto', color: '#fff', borderColor: 'rgba(255,255,255,0.2)', background: 'rgba(255,255,255,0.1)' }}
                        title="Toggle theme"
                    >
                        {theme === 'dark' ? '☀️' : '🌙'}
                    </button>
                </div>

                <div className="ll-hero">
                    <span className="ll-tag">AI-powered learning</span>
                    <h1>
                        Your intelligent<br />
                        <span>academic assistant</span>
                    </h1>
                    <p>
                        Powered by state-of-the-art language models. Get instant help with
                        coding, analysis, research, writing, and much more.
                    </p>
                </div>

                <div className="ll-features">
                    <div className="ll-feat">
                        <div className="ll-feat-icon">🧠</div>
                        <span>Dual AI models — general intelligence & expert coding</span>
                    </div>
                    <div className="ll-feat">
                        <div className="ll-feat-icon">💬</div>
                        <span>Full conversation history, pick up where you left off</span>
                    </div>
                    <div className="ll-feat">
                        <div className="ll-feat-icon">🔒</div>
                        <span>Secure personal accounts with private API access</span>
                    </div>
                </div>
            </div>

            {/* ── RIGHT PANEL ── */}
            <div className="login-right">
                <div className="login-form-wrap">
                    <div className="lf-header">
                        <h2>{tab === 'login' ? 'Welcome back' : 'Create account'}</h2>
                        <p>{tab === 'login' ? 'Sign in to continue' : 'Join JITD AI today'}</p>
                    </div>

                    {/* Google */}
                    <button className="google-btn" onClick={handleGoogle}>
                        <svg width="18" height="18" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                        </svg>
                        Continue with Google
                    </button>

                    <div className="divider">or</div>

                    {/* Tabs */}
                    <div className="auth-tabs">
                        <button className={`auth-tab ${tab === 'login' ? 'active' : ''}`} onClick={() => { setTab('login'); setError(''); }}>Sign in</button>
                        <button className={`auth-tab ${tab === 'register' ? 'active' : ''}`} onClick={() => { setTab('register'); setError(''); }}>Sign up</button>
                    </div>

                    {/* Login Form */}
                    {tab === 'login' && (
                        <form onSubmit={handleLogin}>
                            <div className="field">
                                <label>Username or email</label>
                                <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Enter your username" required autoComplete="username" />
                            </div>
                            <div className="field">
                                <label>Password</label>
                                <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter your password" required autoComplete="current-password" />
                            </div>
                            {error && <div className="form-error">{error}</div>}
                            <button className="submit-btn" type="submit" disabled={loading}>
                                {loading ? 'Signing in…' : 'Sign in'}
                            </button>
                        </form>
                    )}

                    {/* Register Form */}
                    {tab === 'register' && (
                        <form onSubmit={handleRegister}>
                            <div className="field">
                                <label>Username</label>
                                <input value={rUser} onChange={e => setRUser(e.target.value)} placeholder="Choose a username" required />
                            </div>
                            <div className="field">
                                <label>Email</label>
                                <input type="email" value={rEmail} onChange={e => setREmail(e.target.value)} placeholder="your@email.com" required />
                            </div>
                            <div className="field">
                                <label>Password</label>
                                <input type="password" value={rPass} onChange={e => setRPass(e.target.value)} placeholder="Min. 6 characters" required />
                            </div>
                            {error && <div className="form-error">{error}</div>}
                            <button className="submit-btn" type="submit" disabled={loading}>
                                {loading ? 'Creating account…' : 'Create account'}
                            </button>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
}
