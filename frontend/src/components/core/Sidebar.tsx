import { FC } from 'react';
import { QuickAction } from '../../types';
import './Sidebar.css';

interface SidebarProps {
  quickActions: QuickAction[];
  sampleQueries: string[];
  onActionClick: (query: string) => void;
}

export const Sidebar: FC<SidebarProps> = ({ 
  quickActions, 
  sampleQueries, 
  onActionClick 
}) => {
  return (
    <aside className="sidebar">
      <div className="sidebar-content">
        {/* クイックアクション */}
        {quickActions && quickActions.length > 0 && (
          <section className="sidebar-section">
            <h3 className="sidebar-section-title">クイックアクション</h3>
            <div className="quick-actions">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  className="quick-action-btn"
                  onClick={() => onActionClick(action.query)}
                >
                  <span className="quick-action-icon">{action.icon}</span>
                  <span className="quick-action-label">{action.label}</span>
                </button>
              ))}
            </div>
          </section>
        )}
        
        {/* サンプルクエリ */}
        {sampleQueries && sampleQueries.length > 0 && (
          <section className="sidebar-section">
            <h3 className="sidebar-section-title">サンプルクエリ</h3>
            <div className="sample-queries">
              {sampleQueries.map((query, index) => (
                <button
                  key={index}
                  className="sample-query-btn"
                  onClick={() => onActionClick(query)}
                >
                  • {query}
                </button>
              ))}
            </div>
          </section>
        )}
        
        {/* フッター情報 */}
        <div className="sidebar-footer">
          <div className="sidebar-footer-item">
            <span className="sidebar-footer-icon">📊</span>
            <span className="sidebar-footer-text">データドリブン分析</span>
          </div>
          <div className="sidebar-footer-item">
            <span className="sidebar-footer-icon">🤖</span>
            <span className="sidebar-footer-text">AI搭載</span>
          </div>
        </div>
      </div>
    </aside>
  );
};