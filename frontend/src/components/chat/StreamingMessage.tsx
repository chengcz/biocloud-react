/** Streaming message component - shows content as it streams in */

import React from 'react';
import ReactMarkdown from 'react-markdown';

interface StreamingMessageProps {
  content: string;
}

export const StreamingMessage: React.FC<StreamingMessageProps> = ({ content }) => {
  return (
    <div className="flex gap-4 mb-6">
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 text-white"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
        </svg>
      </div>

      {/* Content */}
      <div className="flex-1 max-w-[80%]">
        <div className="inline-block px-4 py-3 rounded-lg bg-gray-700 text-gray-100">
          <div className="prose prose-invert max-w-none">
            <ReactMarkdown>{content || '...'}</ReactMarkdown>
          </div>
          <span className="inline-block w-2 h-4 bg-blue-500 animate-pulse ml-1" />
        </div>
      </div>
    </div>
  );
};

export default StreamingMessage;