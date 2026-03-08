/** Main App component with routing */

import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore, useUIStore } from './stores';
import { Sidebar, ChatContainer } from './components/layout';
import Login from './pages/Login';
import Register from './pages/Register';
import './index.css';

/** Protected route wrapper */
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, token } = useAuthStore();

  if (!isAuthenticated && !token) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

/** Main layout with sidebar and chat */
const MainLayout: React.FC = () => {
  const { toggleSidebar, theme, toggleTheme } = useUIStore();

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <Sidebar />
      <ChatContainer />

      {/* Theme toggle button */}
      <button
        onClick={toggleTheme}
        className="fixed bottom-4 right-4 p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
      >
        {theme === 'dark' ? '☀️' : '🌙'}
      </button>

      {/* Sidebar toggle button */}
      <button
        onClick={toggleSidebar}
        className="fixed top-4 right-4 p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
            clipRule="evenodd"
          />
        </svg>
      </button>
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
      const { state } = JSON.parse(stored);
      if (state?.theme) {
        setTheme(state.theme);
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
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;