/**
 * ドメインカードコンポーネント
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { DomainInfo } from '../../types/domain';
import { ROUTES } from '../../utils/constants';
import './DomainCard.css';

interface DomainCardProps {
  domain: DomainInfo;
  onRequest: (domainId: string) => void;
  onRevoke: (domainId: string) => void;
  loading?: boolean;
}

export const DomainCard: React.FC<DomainCardProps> = ({
  domain,
  onRequest,
  onRevoke,
  loading = false,
}) => {
  const navigate = useNavigate();

  const getStatusLabel = (status: string) => {
    const labels: Record<string, { text: string; emoji: string }> = {
      active: { text: '利用中', emoji: '✅' },
      pending: { text: '申請中', emoji: '⏳' },
      available: { text: '申請可能', emoji: '➕' },
    };
    return labels[status] || labels.available;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const handleRequestClick = () => {
    if (loading) return;
    onRequest(domain.domain_id);
  };

  const handleRevokeClick = () => {
    if (loading) return;
    if (confirm(`${domain.name}のアクセスを取り消しますか？`)) {
      onRevoke(domain.domain_id);
    }
  };

  const handleChatClick = () => {
    navigate(`${ROUTES.CHAT}?domain=${domain.domain_id}`);
  };

  const statusLabel = getStatusLabel(domain.access_status);

  return (
    <div className={`domain-card ${domain.access_status}`}>
      <div className="domain-card-header">
        <div className="domain-icon">{domain.icon}</div>
        <div className="domain-info">
          <h3 className="domain-name">{domain.name}</h3>
          <p className="domain-description">{domain.description}</p>
        </div>
        <div className={`status-badge ${domain.access_status}`}>
          <span className="status-emoji">{statusLabel.emoji}</span>
          <span className="status-text">{statusLabel.text}</span>
        </div>
      </div>

      {domain.access_status !== 'available' && (
        <div className="domain-dates">
          {domain.requested_at && (
            <div className="date-item">
              <span className="date-label">申請日:</span>
              <span className="date-value">{formatDate(domain.requested_at)}</span>
            </div>
          )}
          {domain.approved_at && (
            <div className="date-item">
              <span className="date-label">承認日:</span>
              <span className="date-value">{formatDate(domain.approved_at)}</span>
            </div>
          )}
        </div>
      )}

      <div className="domain-card-actions">
        {domain.access_status === 'active' && (
          <>
            <button
              className="action-btn primary"
              onClick={handleChatClick}
              disabled={loading}
            >
              チャットを開く
            </button>
            <button
              className="action-btn secondary"
              onClick={handleRevokeClick}
              disabled={loading}
            >
              アクセス取り消し
            </button>
          </>
        )}

        {domain.access_status === 'pending' && (
          <>
            <span className="pending-text">承認待ち...</span>
            <button
              className="action-btn secondary"
              onClick={handleRevokeClick}
              disabled={loading}
            >
              申請を取り消す
            </button>
          </>
        )}

        {domain.access_status === 'available' && (
          <button
            className="action-btn primary"
            onClick={handleRequestClick}
            disabled={loading}
          >
            {loading ? '申請中...' : '申請する'}
          </button>
        )}
      </div>
    </div>
  );
};