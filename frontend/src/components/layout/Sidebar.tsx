/** Sidebar component - DeepSeek style conversation list */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useChatStore, useUIStore, useAuthStore } from '../../stores';
import { cn } from '../../utils/cn';

export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const {
    conversations,
    currentConversation,
    selectConversation,
    createConversation,
    deleteConversation,
    fetchConversations,
  } = useChatStore();
  const { sidebarOpen, toggleSidebar, theme, toggleTheme } = useUIStore();
  const { user, token, logout } = useAuthStore();

  // Load conversations when authenticated
  React.useEffect(() => {
    if (token) {
      fetchConversations();
    }
  }, [token, fetchConversations]);

  const handleNewChat = async () => {
    if (!token) {
      // Allow anonymous chat - just close sidebar
      return;
    }
    await createConversation();
  };

  const handleSelectChat = async (id: number) => {
    if (!token) {
      navigate('/login');
      return;
    }
    await selectConversation(id);
  };

  const handleDeleteChat = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!token) return;
    await deleteConversation(id);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  if (!sidebarOpen) return null;

  return (
    <aside className="w-64 bg-gray-50 dark:bg-gray-800/95 backdrop-blur-sm h-screen flex flex-col border-r border-gray-200 dark:border-gray-700/50 transition-colors duration-200">
      {/* Top buttons row */}
      <div className="p-3 flex items-center gap-2">
        {/* Sidebar toggle button - inside sidebar */}
        <button
          onClick={toggleSidebar}
          className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          title="收起侧边栏"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-600 dark:text-gray-300" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h6a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
        </button>

        {/* New Chat Button */}
        <button
          onClick={handleNewChat}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-900 dark:text-white text-sm font-medium"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
          </svg>
          新对话
        </button>

        {/* Theme toggle button */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          title="切换主题"
        >
          {theme === 'dark' ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-600" viewBox="0 0 20 20" fill="currentColor">
              <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
            </svg>
          )}
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto px-2">
        {!token ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
            <p className="mb-3">登录后查看对话历史</p>
            <button
              onClick={() => navigate('/login')}
              className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-500 transition-colors text-white text-sm"
            >
              去登录
            </button>
          </div>
        ) : conversations.length === 0 ? (
          <div className="text-center py-8 text-gray-400 dark:text-gray-500 text-sm">
            暂无对话记录
          </div>
        ) : (
          <div className="space-y-1">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => handleSelectChat(conv.id)}
                className={cn(
                  'group flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200',
                  currentConversation?.id === conv.id
                    ? 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/50'
                )}
              >
                <div className="flex items-center gap-2 truncate">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 flex-shrink-0 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                  </svg>
                  <span className="truncate text-sm">{conv.title}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteChat(e, conv.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-all"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* User Info */}
      <div className="p-3 border-t border-gray-200 dark:border-gray-700/50">
        {token && user ? (
          <div className="flex items-center justify-between px-2 py-2">
            <div className="flex items-center gap-3 text-gray-700 dark:text-gray-300">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-medium text-sm">
                {user.name?.charAt(0) || 'U'}
              </div>
              <span className="text-sm truncate">{user.name || user.username}</span>
            </div>
            <button
              onClick={handleLogout}
              className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
            >
              退出
            </button>
          </div>
        ) : (
          <div className="text-center text-gray-400 dark:text-gray-500 text-sm py-2">
            未登录
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;