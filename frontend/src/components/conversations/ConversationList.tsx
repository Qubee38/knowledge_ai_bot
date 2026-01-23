/**
 * 会話一覧コンポーネント
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { conversationsService } from '../../services/conversations.service';
import { Conversation } from '../../types/conversation';
import { ROUTES } from '../../utils/constants';
import './ConversationList.css';

interface ConversationListProps {
  selectedDomain?: string;
  onConversationSelect?: (conversationId: string) => void;
}

export const ConversationList: React.FC<ConversationListProps> = ({
  selectedDomain,
  onConversationSelect,
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const navigate = useNavigate();

  const limit = 20;

  useEffect(() => {
    loadConversations();
  }, [selectedDomain]);

  const loadConversations = async (append = false) => {
    try {
      setLoading(true);
      const response = await conversationsService.getConversations({
        limit,
        offset: append ? offset : 0,
        domain: selectedDomain,
      });

      if (append) {
        setConversations((prev) => [...prev, ...response.conversations]);
      } else {
        setConversations(response.conversations);
        setOffset(0);
      }

      setHasMore(response.has_more);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = () => {
    const newOffset = offset + limit;
    setOffset(newOffset);
    loadConversations(true);
  };

  const handleDelete = async (conversationId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm('この会話を削除しますか？')) {
      return;
    }

    try {
      await conversationsService.deleteConversation(conversationId);
      setConversations((prev) =>
        prev.filter((c) => c.conversation_id !== conversationId)
      );
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      alert('削除に失敗しました');
    }
  };

  const handleConversationClick = (conversationId: string) => {
    if (onConversationSelect) {
      onConversationSelect(conversationId);
    } else {
      navigate(`${ROUTES.CHAT}?conversation=${conversationId}`);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'たった今';
    if (diffMins < 60) return `${diffMins}分前`;
    if (diffHours < 24) return `${diffHours}時間前`;
    if (diffDays < 7) return `${diffDays}日前`;

    return date.toLocaleDateString('ja-JP');
  };

  const getDomainIcon = (domain: string) => {
    const icons: Record<string, string> = {
      'horse-racing': '🏇',
      'customer-support': '💬',
      'knowledge-base': '📚',
    };
    return icons[domain] || '💬';
  };

  if (loading && conversations.length === 0) {
    return (
      <div className="conversation-list-loading">
        <div className="spinner">読み込み中...</div>
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className="conversation-list-empty">
        <p>会話履歴がありません</p>
        <button
          className="new-conversation-button"
          onClick={() => navigate(ROUTES.CHAT)}
        >
          新しい会話を始める
        </button>
      </div>
    );
  }

  return (
    <div className="conversation-list">
      {conversations.map((conversation) => (
        <div
          key={conversation.conversation_id}
          className="conversation-item"
          onClick={() => handleConversationClick(conversation.conversation_id)}
        >
          <div className="conversation-header">
            <span className="conversation-domain-icon">
              {getDomainIcon(conversation.domain)}
            </span>
            <span className="conversation-title">{conversation.title}</span>
            {conversation.is_pinned && (
              <span className="pin-icon" title="ピン留め">
                📌
              </span>
            )}
          </div>

          <div className="conversation-meta">
            <span className="message-count">
              {conversation.message_count}メッセージ
            </span>
            <span className="separator">•</span>
            <span className="updated-time">
              {formatDate(conversation.updated_at)}
            </span>
          </div>

          <div className="conversation-actions">
            <button
              className="action-button continue"
              onClick={(e) => {
                e.stopPropagation();
                handleConversationClick(conversation.conversation_id);
              }}
            >
              続ける
            </button>
            <button
              className="action-button delete"
              onClick={(e) => handleDelete(conversation.conversation_id, e)}
            >
              削除
            </button>
          </div>
        </div>
      ))}

      {hasMore && (
        <button
          className="load-more-button"
          onClick={handleLoadMore}
          disabled={loading}
        >
          {loading ? '読み込み中...' : 'さらに読み込む'}
        </button>
      )}
    </div>
  );
};