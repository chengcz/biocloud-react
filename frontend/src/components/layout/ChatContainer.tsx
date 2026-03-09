/** Main chat container component - DeepSeek style */

import React, { useRef, useEffect, useState } from 'react';
import { useChatStore, useUIStore } from '../../stores';
import { MessageItem } from '../chat/MessageItem';
import { ChatInput } from '../chat/ChatInput';
import { StreamingMessage } from '../chat/StreamingMessage';

export const ChatContainer: React.FC = () => {
  const { messages, isStreaming, streamingContent, currentConversation } = useChatStore();
  const { sidebarOpen, toggleSidebar, theme, toggleTheme } = useUIStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showWelcome, setShowWelcome] = useState(true);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Hide welcome when conversation is selected or messages exist
  useEffect(() => {
    if (currentConversation || messages.length > 0) {
      setShowWelcome(false);
    }
  }, [currentConversation, messages]);

  return (
    <div className="flex-1 flex flex-col h-screen bg-white dark:bg-gray-900 transition-colors duration-200">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {showWelcome ? (
          <WelcomeScreen />
        ) : (
          <div className="max-w-3xl mx-auto py-4 px-4">
            {messages.map((message) => (
              <MessageItem key={message.id} message={message} />
            ))}
            {isStreaming && <StreamingMessage content={streamingContent} />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area - Fixed at bottom */}
      <div className="border-t border-gray-200 dark:border-gray-700/50 p-4 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm transition-colors duration-200">
        <div className="max-w-3xl mx-auto">
          <ChatInput />
          <p className="text-center text-xs text-gray-400 dark:text-gray-500 mt-2">
            BioCloud 可能会犯错，请核查重要信息
          </p>
        </div>
      </div>

      {/* Floating buttons when sidebar is closed */}
      {!sidebarOpen && (
        <>
          {/* Toggle sidebar button */}
          <button
            onClick={toggleSidebar}
            className="fixed top-4 left-4 p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors border border-gray-200 dark:border-gray-700"
            title="展开侧边栏"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-600 dark:text-gray-300" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" />
            </svg>
          </button>

          {/* Theme toggle button */}
          <button
            onClick={toggleTheme}
            className="fixed top-4 right-4 p-2 rounded-lg bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors border border-gray-200 dark:border-gray-700"
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
        </>
      )}
    </div>
  );
};

/** Welcome screen - DeepSeek style centered layout */
const WelcomeScreen: React.FC = () => {
  const suggestions = [
    {
      title: '火山图分析',
      description: '上传差异表达数据，生成火山图',
      icon: '🌋',
    },
    {
      title: 'GO富集分析',
      description: '分析基因功能富集情况',
      icon: '📊',
    },
    {
      title: 'SNP密度图',
      description: '可视化SNP分布情况',
      icon: '🧬',
    },
    {
      title: '微生物组分析',
      description: '物种组成和多样性分析',
      icon: '🔬',
    },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center h-full px-4">
      {/* Logo and Title */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">BioCloud</h1>
        <p className="text-gray-500 dark:text-gray-400">基于LLM的生物信息在线分析平台</p>
      </div>

      {/* Suggestion Grid */}
      <div className="grid grid-cols-2 gap-3 max-w-2xl w-full mb-8">
        {suggestions.map((item) => (
          <div
            key={item.title}
            className="group p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 cursor-pointer transition-all duration-200"
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">{item.icon}</span>
              <div>
                <h3 className="text-gray-900 dark:text-white font-medium mb-1">{item.title}</h3>
                <p className="text-gray-500 dark:text-gray-400 text-sm">{item.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Tips */}
      <div className="flex flex-wrap justify-center gap-2 text-sm text-gray-400 dark:text-gray-500">
        <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800/50 rounded-full">按 Enter 发送</span>
        <span className="px-3 py-1 bg-gray-100 dark:bg-gray-800/50 rounded-full">Shift + Enter 换行</span>
      </div>
    </div>
  );
};

export default ChatContainer;