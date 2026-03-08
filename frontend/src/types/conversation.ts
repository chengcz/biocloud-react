/** Conversation-related types */

export interface Conversation {
  id: number;
  user_id: number;
  title: string;
  model: string;
  is_archived: boolean;
  last_message_at?: string;
  create_time: string;
  messages?: Message[];
}

export interface ConversationCreate {
  title?: string;
  model?: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, unknown>;
  create_time: string;
}

export interface MessageCreate {
  content: string;
  role?: 'user';
}