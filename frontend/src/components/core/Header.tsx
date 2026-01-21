import { FC } from 'react';
import './Header.css';

interface HeaderProps {
  appName: string;
  appDescription: string;
  onMenuClick: () => void;
}

export const Header: FC<HeaderProps> = ({ appName, appDescription, onMenuClick }) => {
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
        <button className="header-action-btn" title="Settings">
          ⚙️
        </button>
        <button className="header-action-btn" title="Help">
          ❓
        </button>
        <button className="header-action-btn" title="Account">
          👤
        </button>
      </div>
    </header>
  );
};