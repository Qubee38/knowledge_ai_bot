/**
 * ユーザーメニュー（ドロップダウン）
 */
import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { ROUTES } from '../../utils/constants';
import './UserMenu.css';

export const UserMenu: React.FC = () => {
  const { user, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // 外側クリックでメニューを閉じる
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
  };

  const handleDomainsClick = () => {
    setIsOpen(false);
    navigate(ROUTES.DOMAINS);
  };

  if (!user) return null;

  return (
    <div className="user-menu" ref={menuRef}>
      <button
        className="user-menu-button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="User menu"
      >
        <div className="user-avatar">
          {user.display_name ? user.display_name[0].toUpperCase() : user.email[0].toUpperCase()}
        </div>
        <span className="user-name">{user.display_name || user.email}</span>
        <span className="dropdown-arrow">{isOpen ? '▲' : '▼'}</span>
      </button>

      {isOpen && (
        <div className="user-menu-dropdown">
          <div className="user-menu-header">
            <div className="user-menu-email">{user.email}</div>
            {user.display_name && (
              <div className="user-menu-display-name">{user.display_name}</div>
            )}
          </div>

          <div className="user-menu-divider" />

          <button className="user-menu-item" onClick={handleDomainsClick}>
            <span className="menu-icon">📦</span>
            <span>ドメイン管理</span>
          </button>

          <button className="user-menu-item" onClick={() => setIsOpen(false)}>
            <span className="menu-icon">⚙️</span>
            <span>設定</span>
          </button>

          <div className="user-menu-divider" />

          <button className="user-menu-item logout" onClick={handleLogout}>
            <span className="menu-icon">🚪</span>
            <span>ログアウト</span>
          </button>
        </div>
      )}
    </div>
  );
};