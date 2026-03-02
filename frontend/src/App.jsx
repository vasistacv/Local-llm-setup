import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, AuthProvider, useAuth } from './context';
import { fetchMe, getToken } from './utils/api';
import LoginPage from './pages/LoginPage';
import ChatPage from './pages/ChatPage';
import './index.css';

function AppRoutes() {
    const { user, setUser, ready, setReady } = useAuth();

    useEffect(() => {
        const token = getToken();
        if (!token) { setReady(true); return; }
        fetchMe()
            .then(me => { setUser(me); setReady(true); })
            .catch(() => { setReady(true); });
    }, []);

    if (!ready) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 32, marginBottom: 16 }}>✦</div>
                    <div style={{ fontSize: 14, color: 'var(--text3)' }}>Loading JITD AI…</div>
                </div>
            </div>
        );
    }

    return (
        <Routes>
            <Route path="/" element={user ? <Navigate to="/chat" replace /> : <LoginPage />} />
            <Route path="/chat" element={user ? <ChatPage /> : <Navigate to="/" replace />} />
            <Route path="*" element={<Navigate to={user ? '/chat' : '/'} replace />} />
        </Routes>
    );
}

export default function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <BrowserRouter>
                    <AppRoutes />
                </BrowserRouter>
            </AuthProvider>
        </ThemeProvider>
    );
}
