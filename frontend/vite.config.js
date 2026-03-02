import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
    plugins: [react()],
    build: {
        outDir: path.resolve(__dirname, '../ui'),
        emptyOutDir: true,
    },
    server: {
        proxy: {
            '/auth': 'http://localhost:8000',
            '/chat': 'http://localhost:8000',
            '/conversations': 'http://localhost:8000',
            '/api': 'http://localhost:8000',
        }
    }
})
