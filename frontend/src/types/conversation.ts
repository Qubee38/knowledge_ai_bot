/**
 * 会話関連の型定義
 */

export interface Conversation {
  conversation_id: string;
  domain: string;
  title: string;
  message_count: number;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  is_archived: boolean;
  messages: Message[];
}

export interface Message {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ConversationsResponse {
  conversations: Conversation[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface CreateConversationRequest {
  domain: string;
  title?: string;
}

export interface UpdateConversationRequest {
  title?: string;
  is_pinned?: boolean;
}