/** Sidebar component - ChatGPT style conversation list */

import React from 'react';
import { useChatStore, useUIStore } from '../stores';
import { cn } from '../utils/cn';

export const Sidebar: React.FC = () => {
  const {
    conversations,
    currentConversation,
    selectConversation,
    createConversation,
    deleteConversation,
  } = useChatStore();
  const { sidebarOpen } = useUIStore();

  const handleNewChat = async () => {
    await createConversation();
  };

  const handleSelectChat = async (id: number) => {
    await selectConversation(id);
  };

  const handleDeleteChat = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    await deleteConversation(id);
  };

  if (!sidebarOpen) return null;

  return (
    <aside className="w-64 bg-gray-900 h-screen flex flex-col border-r border-gray-700">
      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg border border-gray-600 hover:bg-gray-700 transition-colors text-white"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
              clipRule="evenodd"
            />
          </svg>
          新对话
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto px-2">
        <div className="space-y-1">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => handleSelectChat(conv.id)}
              className={cn(
                'group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors',
                currentConversation?.id === conv.id
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-300 hover:bg-gray-700/50'
              )}
            >
              <div className="flex items-center gap-2 truncate">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4 flex-shrink-0"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="truncate text-sm">{conv.title}</span>
              </div>
              <button
                onClick={(e) => handleDeleteChat(e, conv.id)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition-opacity"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* User Info */}
      <div className="p-3 border-t border-gray-700">
        <div className="flex items-center gap-3 px-2 py-2 text-gray-300">
          <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <span className="text-sm truncate">用户</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;