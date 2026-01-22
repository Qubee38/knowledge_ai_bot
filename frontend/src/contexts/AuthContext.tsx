/**
 * 認証コンテキスト
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoginRequest, RegisterRequest, AuthState } from '../types/auth';
import { authService } from '../services/auth.service';
import { storage } from '../utils/storage';
import { ROUTES } from '../utils/constants';

interface AuthContextType extends AuthState {
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    tokens: null,
    isAuthenticated: false,
    isLoading: true,
  });

  const navigate = useNavigate();

  // 初期化: ローカルストレージからユーザー情報復元
  useEffect(() => {
    const initAuth = async () => {
      const accessToken = storage.getAccessToken();
      const user = storage.getUser();

      if (accessToken && user && !storage.isTokenExpired()) {
        // トークンが有効な場合
        setState({
          user,
          tokens: {
            accessToken,
            refreshToken: storage.getRefreshToken() || '',
            expiresIn: 0,
          },
          isAuthenticated: true,
          isLoading: false,
        });

        // ユーザー情報を最新化
        try {
          const currentUser = await authService.getCurrentUser();
          storage.setUser(currentUser);
          setState((prev) => ({ ...prev, user: currentUser }));
        } catch (error) {
          console.error('Failed to refresh user:', error);
          // トークンが無効な場合はログアウト
          storage.clearAll();
          setState({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      } else {
        // トークンがない、または期限切れ
        storage.clearAll();
        setState({
          user: null,
          tokens: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    };

    initAuth();
  }, []);

  /**
   * ログイン
   */
  const login = async (data: LoginRequest) => {
    try {
      const response = await authService.login(data);

      // トークン保存
      storage.setTokens(
        response.access_token,
        response.refresh_token,
        response.expires_in
      );

      // ユーザー情報保存
      storage.setUser(response.user);

      // ステート更新
      setState({
        user: response.user,
        tokens: {
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
          expiresIn: response.expires_in,
        },
        isAuthenticated: true,
        isLoading: false,
      });

      // チャット画面へリダイレクト
      navigate(ROUTES.CHAT);
    } catch (error: any) {
      console.error('Login failed:', error);
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  };

  /**
   * ユーザー登録
   */
  const register = async (data: RegisterRequest) => {
    try {
    //   const user = await authService.register(data);

      // 登録後、自動ログイン
      await login({
        email: data.email,
        password: data.password,
      });
    } catch (error: any) {
      console.error('Registration failed:', error);
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  };

  /**
   * ログアウト
   */
  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // ローカルストレージクリア
      storage.clearAll();

      // ステート更新
      setState({
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
      });

      // ログイン画面へリダイレクト
      navigate(ROUTES.LOGIN);
    }
  };

  /**
   * ユーザー情報更新
   */
  const refreshUser = async () => {
    try {
      const user = await authService.getCurrentUser();
      storage.setUser(user);
      setState((prev) => ({ ...prev, user }));
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * useAuth Hook
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};