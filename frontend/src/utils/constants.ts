/**
 * 定数定義
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const WS_BASE_URL = API_BASE_URL.replace('http', 'ws');

export const API_ENDPOINTS = {
  // 認証
  AUTH_REGISTER: '/api/auth/register',
  AUTH_LOGIN: '/api/auth/login',
  AUTH_LOGOUT: '/api/auth/logout',
  AUTH_ME: '/api/auth/me',
  AUTH_REFRESH: '/api/auth/refresh',
  
  // ドメイン
  DOMAINS: '/api/domains',
  DOMAIN_REQUEST: (domainId: string) => `/api/domains/${domainId}/request`,
  DOMAIN_REVOKE: (domainId: string) => `/api/domains/${domainId}/access`,
  DOMAIN_CHECK: (domainId: string) => `/api/domains/check-access/${domainId}`,
  
  // 設定
  CONFIG_DOMAIN: '/api/config/domain',
  
  // チャット
  CHAT_MESSAGE: '/api/chat/message',
  CHAT_WS: '/ws/chat',
} as const;

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  CHAT: '/chat',
  DOMAINS: '/domains',
} as const;