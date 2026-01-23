/**
 * 会話履歴ページ
 */
import React, { useState } from 'react';
import { ConversationList } from '../components/conversations/ConversationList';
import './ConversationsPage.css';

export const ConversationsPage: React.FC = () => {
  const [selectedDomain, setSelectedDomain] = useState<string | undefined>(
    undefined
  );

  const domains = [
    { id: undefined, name: 'すべて', icon: '📚' },
    { id: 'horse-racing', name: '競馬', icon: '🏇' },
    { id: 'customer-support', name: 'サポート', icon: '💬' },
  ];

  return (
    <div className="conversations-page">
      <div className="conversations-header">
        <h1>📚 会話履歴</h1>
        <p>過去の会話を確認できます</p>
      </div>

      <div className="domain-filters">
        {domains.map((domain) => (
          <button
            key={domain.id || 'all'}
            className={`domain-filter ${
              selectedDomain === domain.id ? 'active' : ''
            }`}
            onClick={() => setSelectedDomain(domain.id)}
          >
            <span className="filter-icon">{domain.icon}</span>
            <span className="filter-name">{domain.name}</span>
          </button>
        ))}
      </div>

      <ConversationList selectedDomain={selectedDomain} />
    </div>
  );
};