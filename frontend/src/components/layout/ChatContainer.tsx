/** Main chat container component */

import React, { useRef, useEffect, useState } from 'react';
import { useChatStore } from '../../stores';
import { MessageItem } from '../chat/MessageItem';
import { ChatInput } from '../chat/ChatInput';
import { StreamingMessage } from '../chat/StreamingMessage';

export const ChatContainer: React.FC = () => {
  const { messages, isStreaming, streamingContent, currentConversation } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showWelcome, setShowWelcome] = useState(true);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Hide welcome when conversation is selected
  useEffect(() => {
    if (currentConversation || messages.length > 0) {
      setShowWelcome(false);
    }
  }, [currentConversation, messages]);

  return (
    <div className="flex-1 flex flex-col h-screen bg-gray-800">
      {/* Header */}
      <header className="h-14 border-b border-gray-700 flex items-center justify-between px-4">
        <h1 className="text-white font-medium">
          {currentConversation?.title || 'BioCloud'}
        </h1>
        <div className="text-gray-400 text-sm">
          {currentConversation?.model || 'claude'}
        </div>
      </header>

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

      {/* Input Area */}
      <div className="border-t border-gray-700 p-4">
        <div className="max-w-3xl mx-auto">
          <ChatInput />
        </div>
      </div>
    </div>
  );
};

/** Welcome screen shown when no conversation is selected */
const WelcomeScreen: React.FC = () => {
  const suggestions = [
    { title: '火山图分析', description: '上传差异表达数据，生成火山图' },
    { title: 'GO富集分析', description: '分析基因功能富集情况' },
    { title: 'SNP密度图', description: '可视化SNP分布情况' },
    { title: '微生物组分析', description: '物种组成和多样性分析' },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center h-full text-center px-4">
      <h1 className="text-4xl font-bold text-white mb-2">BioCloud</h1>
      <p className="text-gray-400 mb-8">基于LLM的生物信息在线分析平台</p>

      <div className="grid grid-cols-2 gap-4 max-w-2xl">
        {suggestions.map((item, index) => (
          <div
            key={index}
            className="p-4 bg-gray-700/50 rounded-lg border border-gray-600 hover:bg-gray-700 cursor-pointer transition-colors"
          >
            <h3 className="text-white font-medium mb-1">{item.title}</h3>
            <p className="text-gray-400 text-sm">{item.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChatContainer;