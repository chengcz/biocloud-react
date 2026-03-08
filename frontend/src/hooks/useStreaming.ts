/** Hook for streaming SSE responses */

import { useState, useCallback } from 'react';
import { conversationApi } from '../api';

interface UseStreamingOptions {
  conversationId: number;
  onComplete?: () => void;
  onError?: (error: Error) => void;
}

export function useStreaming({ conversationId, onComplete, onError }: UseStreamingOptions) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      setIsStreaming(true);
      setStreamingContent('');
      setError(null);

      await conversationApi.sendMessage(
        conversationId,
        { content },
        (chunk) => {
          setStreamingContent((prev) => prev + chunk);
        },
        () => {
          setIsStreaming(false);
          setStreamingContent('');
          onComplete?.();
        },
        (err) => {
          setIsStreaming(false);
          setError(err.message);
          onError?.(err);
        }
      );
    },
    [conversationId, onComplete, onError]
  );

  return {
    isStreaming,
    streamingContent,
    error,
    sendMessage,
  };
}

export default useStreaming;