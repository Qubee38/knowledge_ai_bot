import { FC } from 'react';
import { UserMenu } from '../auth/UserMenu';
import { useAuth } from '../../hooks/useAuth';
import './Header.css';

interface HeaderProps {
  appName: string;
  appDescription: string;
  onMenuClick: () => void;
}

export const Header: FC<HeaderProps> = ({ appName, appDescription, onMenuClick }) => {
  const { isAuthenticated } = useAuth();

  return (
    <header className="header">
      <div className="header-left">
        <button 
          className="menu-button"
          onClick={onMenuClick}
          aria-label="Toggle menu"
        >
          ☰
        </button>
        
        <div className="header-brand">
          <div className="header-icon">🏇</div>
          <div className="header-info">
            <h1 className="header-title">{appName}</h1>
            <p className="header-description">{appDescription}</p>
          </div>
        </div>
      </div>
      
      <div className="header-right">
        {isAuthenticated ? (
          // 認証済み: ユーザーメニュー表示
          <UserMenu />
        ) : (
          // 未認証: 既存のアクションボタン
          <>
            <button className="header-action-btn" title="Settings">
              ⚙️
            </button>
            <button className="header-action-btn" title="Help">
              ❓
            </button>
          </>
        )}
      </div>
    </header>
  );
};