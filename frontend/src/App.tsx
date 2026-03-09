/** Main App component with routing - DeepSeek style */

import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore, useUIStore } from './stores';
import { Sidebar, ChatContainer } from './components/layout';
import Login from './pages/Login';
import Register from './pages/Register';
import './index.css';

/** Main layout with sidebar and chat - DeepSeek style */
const MainLayout: React.FC = () => {
  const { token } = useAuthStore();

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white transition-colors duration-200">
      {/* Sidebar - collapsible */}
      <Sidebar />

      {/* Main Chat Area */}
      <ChatContainer />

      {/* Login button (show when not logged in) */}
      {!token && (
        <a
          href="/login"
          className="fixed top-4 right-4 px-4 py-2 rounded-full bg-blue-600 hover:bg-blue-500 transition-colors text-sm font-medium shadow-lg text-white"
        >
          登录
        </a>
      )}
    </div>
  );
};

/** App component */
const App: React.FC = () => {
  const { fetchCurrentUser, token } = useAuthStore();
  const { setTheme } = useUIStore();

  // Initialize theme from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('ui-storage');
    if (stored) {
      try {
        const { state } = JSON.parse(stored);
        if (state?.theme) {
          setTheme(state.theme);
        }
      } catch {
        // Ignore parse errors
      }
    }
  }, [setTheme]);

  // Fetch current user on mount if token exists
  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    }
  }, [token, fetchCurrentUser]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<MainLayout />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;