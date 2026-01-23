/**
 * ドメイン一覧コンポーネント
 */
import React, { useState, useEffect } from 'react';
import { domainsService } from '../../services/domains.service';
import { DomainInfo } from '../../types/domain';
import { DomainCard } from './DomainCard';
import './DomainList.css';

export const DomainList: React.FC = () => {
  const [domains, setDomains] = useState<DomainInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    loadDomains();
  }, []);

  const loadDomains = async () => {
    try {
      setLoading(true);
      const response = await domainsService.getDomains();
      setDomains(response.domains);
    } catch (error) {
      console.error('Failed to load domains:', error);
      alert('ドメイン一覧の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleRequest = async (domainId: string) => {
    try {
      setActionLoading(domainId);
      await domainsService.requestDomainAccess(domainId, {
        reason: 'ドメインアクセスを申請します',
      });
      
      // ドメイン一覧を再取得
      await loadDomains();
      
      alert('ドメインアクセスが承認されました！');
    } catch (error: any) {
      console.error('Failed to request domain access:', error);
      const message =
        error.response?.data?.detail || 'ドメインアクセス申請に失敗しました';
      alert(message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRevoke = async (domainId: string) => {
    try {
      setActionLoading(domainId);
      await domainsService.revokeDomainAccess(domainId);
      
      // ドメイン一覧を再取得
      await loadDomains();
      
      alert('ドメインアクセスを取り消しました');
    } catch (error: any) {
      console.error('Failed to revoke domain access:', error);
      const message =
        error.response?.data?.detail || 'ドメインアクセス取り消しに失敗しました';
      alert(message);
    } finally {
      setActionLoading(null);
    }
  };

  const groupedDomains = {
    active: domains.filter((d) => d.access_status === 'active'),
    pending: domains.filter((d) => d.access_status === 'pending'),
    available: domains.filter((d) => d.access_status === 'available'),
  };

  if (loading) {
    return (
      <div className="domain-list-loading">
        <div className="spinner">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="domain-list">
      {groupedDomains.active.length > 0 && (
        <div className="domain-section">
          <h2 className="section-title">
            <span className="section-icon">✅</span>
            利用中
          </h2>
          <div className="domain-grid">
            {groupedDomains.active.map((domain) => (
              <DomainCard
                key={domain.domain_id}
                domain={domain}
                onRequest={handleRequest}
                onRevoke={handleRevoke}
                loading={actionLoading === domain.domain_id}
              />
            ))}
          </div>
        </div>
      )}

      {groupedDomains.pending.length > 0 && (
        <div className="domain-section">
          <h2 className="section-title">
            <span className="section-icon">⏳</span>
            申請中
          </h2>
          <div className="domain-grid">
            {groupedDomains.pending.map((domain) => (
              <DomainCard
                key={domain.domain_id}
                domain={domain}
                onRequest={handleRequest}
                onRevoke={handleRevoke}
                loading={actionLoading === domain.domain_id}
              />
            ))}
          </div>
        </div>
      )}

      {groupedDomains.available.length > 0 && (
        <div className="domain-section">
          <h2 className="section-title">
            <span className="section-icon">➕</span>
            申請可能
          </h2>
          <div className="domain-grid">
            {groupedDomains.available.map((domain) => (
              <DomainCard
                key={domain.domain_id}
                domain={domain}
                onRequest={handleRequest}
                onRevoke={handleRevoke}
                loading={actionLoading === domain.domain_id}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};