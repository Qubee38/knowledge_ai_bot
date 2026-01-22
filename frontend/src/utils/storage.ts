/**
 * LocalStorage管理ユーティリティ
 */

const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  TOKEN_EXPIRES_AT: 'token_expires_at',
  USER: 'user',
} as const;

export const storage = {
  // トークン保存
  setTokens(accessToken: string, refreshToken: string, expiresIn: number) {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, accessToken);
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
    
    const expiresAt = Date.now() + expiresIn * 1000;
    localStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRES_AT, expiresAt.toString());
  },

  // トークン取得
  getAccessToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  },

  getRefreshToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  },

  // トークン有効期限チェック
  isTokenExpired(): boolean {
    const expiresAt = localStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRES_AT);
    if (!expiresAt) return true;
    
    return Date.now() > parseInt(expiresAt, 10);
  },

  // トークンクリア
  clearTokens() {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.TOKEN_EXPIRES_AT);
  },

  // ユーザー情報保存
  setUser(user: any) {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
  },

  // ユーザー情報取得
  getUser(): any | null {
    const userStr = localStorage.getItem(STORAGE_KEYS.USER);
    if (!userStr) return null;
    
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  },

  // ユーザー情報クリア
  clearUser() {
    localStorage.removeItem(STORAGE_KEYS.USER);
  },

  // 全てクリア
  clearAll() {
    this.clearTokens();
    this.clearUser();
  },
};