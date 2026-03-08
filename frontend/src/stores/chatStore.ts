/** Chat store using Zustand */

import { create } from 'zustand';
import type { Conversation, Message } from '../types';
import { conversationApi } from '../api';

interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  error: string | null;

  // Actions
  fetchConversations: () => Promise<void>;
  selectConversation: (id: number) => Promise<void>;
  createConversation: () => Promise<Conversation>;
  deleteConversation: (id: number) => Promise<void>;
  updateConversationTitle: (id: number, title: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingContent: '',
  error: null,

  fetchConversations: async () => {
    set({ isLoading: true, error: null });
    try {
      const conversations = await conversationApi.list();
      set({ conversations, isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch conversations';
      set({ error: message, isLoading: false });
    }
  },

  selectConversation: async (id: number) => {
    set({ isLoading: true, error: null });
    try {
      const conversation = await conversationApi.get(id);
      set({
        currentConversation: conversation,
        messages: conversation.messages || [],
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch conversation';
      set({ error: message, isLoading: false });
    }
  },

  createConversation: async () => {
    set({ isLoading: true, error: null });
    try {
      const conversation = await conversationApi.create();
      const { conversations } = get();
      set({
        conversations: [conversation, ...conversations],
        currentConversation: conversation,
        messages: [],
        isLoading: false,
      });
      return conversation;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create conversation';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  deleteConversation: async (id: number) => {
    try {
      await conversationApi.delete(id);
      const { conversations, currentConversation } = get();
      const newConversations = conversations.filter((c) => c.id !== id);
      set({
        conversations: newConversations,
        currentConversation:
          currentConversation?.id === id ? null : currentConversation,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete conversation';
      set({ error: message });
    }
  },

  updateConversationTitle: async (id: number, title: string) => {
    try {
      const updated = await conversationApi.updateTitle(id, title);
      const { conversations } = get();
      const newConversations = conversations.map((c) =>
        c.id === id ? updated : c
      );
      set({ conversations: newConversations });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update title';
      set({ error: message });
    }
  },

  sendMessage: async (content: string) => {
    const { currentConversation, messages, createConversation } = get();

    let conversationId = currentConversation?.id;

    // Create conversation if none exists
    if (!conversationId) {
      const newConversation = await createConversation();
      conversationId = newConversation.id;
    }

    // Add user message
    const userMessage: Message = {
      id: Date.now(), // Temporary ID
      conversation_id: conversationId,
      role: 'user',
      content,
      create_time: new Date().toISOString(),
    };

    set({
      messages: [...messages, userMessage],
      isStreaming: true,
      streamingContent: '',
    });

    // Send message and handle streaming
    await conversationApi.sendMessage(
      conversationId,
      { content },
      (chunk) => {
        set((state) => ({
          streamingContent: state.streamingContent + chunk,
        }));
      },
      () => {
        const { streamingContent } = get();
        const assistantMessage: Message = {
          id: Date.now() + 1,
          conversation_id: conversationId!,
          role: 'assistant',
          content: streamingContent,
          create_time: new Date().toISOString(),
        };

        set((state) => ({
          messages: [...state.messages, assistantMessage],
          isStreaming: false,
          streamingContent: '',
        }));
      },
      (error) => {
        set({
          error: error.message,
          isStreaming: false,
          streamingContent: '',
        });
      }
    );
  },

  clearError: () => set({ error: null }),
}));

export default useChatStore;