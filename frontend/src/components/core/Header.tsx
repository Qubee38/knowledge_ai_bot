import { FC } from 'react';
import { useNavigate } from 'react-router-dom';
import { UserMenu } from '../auth/UserMenu';
import { useAuth } from '../../hooks/useAuth';
import { ROUTES } from '../../utils/constants';
import './Header.css';

interface HeaderProps {
  appName: string;
  appDescription: string;
  onMenuClick: () => void;
}

export const Header: FC<HeaderProps> = ({ appName, appDescription, onMenuClick }) => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

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
        
        <div className="header-brand" onClick={() => navigate(ROUTES.CHAT)} style={{ cursor: 'pointer' }}>
          <div className="header-icon">🏇</div>
          <div className="header-info">
            <h1 className="header-title">{appName}</h1>
            <p className="header-description">{appDescription}</p>
          </div>
        </div>
      </div>
      
      <div className="header-right">
        {isAuthenticated ? (
          <>
            {/* クイックアクセスボタン（オプション） */}
            <button
              className="header-action-btn"
              onClick={() => navigate(ROUTES.CONVERSATIONS)}
              title="会話履歴"
            >
              📚
            </button>
            <button
              className="header-action-btn"
              onClick={() => navigate(ROUTES.DOMAINS)}
              title="ドメイン管理"
            >
              📦
            </button>
            
            {/* ユーザーメニュー */}
            <UserMenu />
          </>
        ) : (
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