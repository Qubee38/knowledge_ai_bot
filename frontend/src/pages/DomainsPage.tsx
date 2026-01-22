/**
 * ドメイン管理ページ
 * Phase 1では簡易実装
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '../utils/constants';

export const DomainsPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div style={{ padding: '40px', textAlign: 'center' }}>
      <h1>ドメイン管理</h1>
      <p>Phase 2で実装予定</p>
      <button
        onClick={() => navigate(ROUTES.CHAT)}
        style={{
          marginTop: '20px',
          padding: '12px 24px',
          background: '#667eea',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer',
        }}
      >
        チャットに戻る
      </button>
    </div>
  );
};