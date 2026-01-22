/**
 * API通信基盤
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { API_BASE_URL } from '../utils/constants';
import { storage } from '../utils/storage';

// Axiosインスタンス作成
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// リクエストインターセプター（トークン自動付与）
apiClient.interceptors.request.use(
  (config) => {
    const token = storage.getAccessToken();
    
    if (token && !storage.isTokenExpired()) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// レスポンスインターセプター（エラーハンドリング）
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
    
    // 401エラー（認証エラー）
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // トークンリフレッシュ試行
      // TODO: Phase 2で実装
      // const refreshToken = storage.getRefreshToken();
      // if (refreshToken) {
      //   try {
      //     const { data } = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
      //       refresh_token: refreshToken
      //     });
      //     storage.setTokens(data.access_token, data.refresh_token, data.expires_in);
      //     return apiClient(originalRequest);
      //   } catch (refreshError) {
      //     storage.clearAll();
      //     window.location.href = '/login';
      //   }
      // }
      
      // Phase 1: トークン期限切れの場合はログアウト
      storage.clearAll();
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;