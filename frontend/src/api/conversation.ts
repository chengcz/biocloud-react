/** Conversation API */

import apiClient from './client';
import type { Conversation, ConversationCreate, Message, MessageCreate } from '../types';

export const conversationApi = {
  /** Get all conversations for current user */
  list: async (): Promise<Conversation[]> => {
    const response = await apiClient.get<Conversation[]>('/conversations');
    return response.data;
  },

  /** Get single conversation with messages */
  get: async (id: number): Promise<Conversation> => {
    const response = await apiClient.get<Conversation>(`/conversations/${id}`);
    return response.data;
  },

  /** Create new conversation */
  create: async (data?: ConversationCreate): Promise<Conversation> => {
    const response = await apiClient.post<Conversation>('/conversations', data);
    return response.data;
  },

  /** Delete conversation */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/conversations/${id}`);
  },

  /** Update conversation title */
  updateTitle: async (id: number, title: string): Promise<Conversation> => {
    const response = await apiClient.patch<Conversation>(`/conversations/${id}`, { title });
    return response.data;
  },

  /** Send message and get streaming response (SSE) */
  sendMessage: async (
    conversationId: number,
    message: MessageCreate,
    onChunk: (chunk: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): Promise<void> => {
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || '/api/v1'}/conversations/${conversationId}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(message),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE data lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();

            if (data === '[DONE]') {
              onComplete();
              return;
            }

            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                onChunk(parsed.content);
              } else if (parsed.error) {
                onError(new Error(parsed.error));
              }
            } catch {
              // Ignore parse errors for incomplete JSON
            }
          }
        }
      }

      onComplete();
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Unknown error'));
    }
  },

  /** Get messages for a conversation */
  getMessages: async (conversationId: number): Promise<Message[]> => {
    const response = await apiClient.get<Message[]>(
      `/conversations/${conversationId}/messages`
    );
    return response.data;
  },
};

export default conversationApi;