/**
 * 認証サービス
 */
import apiClient from './api';
import { API_ENDPOINTS } from '../utils/constants';
import { LoginRequest, RegisterRequest, LoginResponse, User } from '../types/auth';

export const authService = {
  /**
   * ユーザー登録
   */
  async register(data: RegisterRequest): Promise<User> {
    const response = await apiClient.post<User>(API_ENDPOINTS.AUTH_REGISTER, data);
    return response.data;
  },

  /**
   * ログイン
   */
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>(API_ENDPOINTS.AUTH_LOGIN, data);
    return response.data;
  },

  /**
   * ログアウト
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post(API_ENDPOINTS.AUTH_LOGOUT);
    } catch (error) {
      console.error('Logout error:', error);
    }
  },

  /**
   * 現在のユーザー情報取得
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>(API_ENDPOINTS.AUTH_ME);
    return response.data;
  },

  /**
   * トークンリフレッシュ
   */
  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>(API_ENDPOINTS.AUTH_REFRESH, {
      refresh_token: refreshToken,
    });
    return response.data;
  },
};