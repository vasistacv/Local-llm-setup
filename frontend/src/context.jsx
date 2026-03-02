import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeCtx = createContext();
const AuthCtx = createContext();

export function ThemeProvider({ children }) {
    const [theme, setTheme] = useState(() => localStorage.getItem('jitd_theme') || 'dark');

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('jitd_theme', theme);
    }, [theme]);

    const toggle = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

    return <ThemeCtx.Provider value={{ theme, toggle }}>{children}</ThemeCtx.Provider>;
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [ready, setReady] = useState(false);

    return (
        <AuthCtx.Provider value={{ user, setUser, ready, setReady }}>
            {children}
        </AuthCtx.Provider>
    );
}

export const useTheme = () => useContext(ThemeCtx);
export const useAuth = () => useContext(AuthCtx);
