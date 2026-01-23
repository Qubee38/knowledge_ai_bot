/**
 * 会話管理サービス
 */
import api from './api';
import {
  Conversation,
  ConversationDetail,
  ConversationsResponse,
  CreateConversationRequest,
  UpdateConversationRequest,
} from '../types/conversation';

export const conversationsService = {
  /**
   * 会話一覧取得
   */
  async getConversations(params?: {
    limit?: number;
    offset?: number;
    domain?: string;
  }): Promise<ConversationsResponse> {
    const response = await api.get<ConversationsResponse>('/api/conversations', {
      params,
    });
    return response.data;
  },

  /**
   * 会話詳細取得
   */
  async getConversation(conversationId: string): Promise<ConversationDetail> {
    const response = await api.get<ConversationDetail>(
      `/api/conversations/${conversationId}`
    );
    return response.data;
  },

  /**
   * 新規会話作成
   */
  async createConversation(
    data: CreateConversationRequest
  ): Promise<Conversation> {
    const response = await api.post<Conversation>('/api/conversations', data);
    return response.data;
  },

  /**
   * 会話更新
   */
  async updateConversation(
    conversationId: string,
    data: UpdateConversationRequest
  ): Promise<Conversation> {
    const response = await api.patch<Conversation>(
      `/api/conversations/${conversationId}`,
      data
    );
    return response.data;
  },

  /**
   * 会話削除
   */
  async deleteConversation(conversationId: string): Promise<void> {
    await api.delete(`/api/conversations/${conversationId}`);
  },
};