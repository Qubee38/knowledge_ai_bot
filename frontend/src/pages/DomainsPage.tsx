/**
 * ドメイン管理ページ
 */
import React from 'react';
import { DomainList } from '../components/domains/DomainList';
import './DomainsPage.css';

export const DomainsPage: React.FC = () => {
  return (
    <div className="domains-page">
      <div className="domains-header">
        <h1>📦 ドメイン管理</h1>
        <p>利用可能なドメインを管理できます</p>
      </div>

      <DomainList />
    </div>
  );
};