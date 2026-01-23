import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ChatPage } from './pages/ChatPage';
import { DomainsPage } from './pages/DomainsPage';
import { ConversationsPage } from './pages/ConversationsPage';
import { ROUTES } from './utils/constants';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* ルート: 認証済みならチャット、未認証ならログイン */}
          <Route path={ROUTES.HOME} element={<Navigate to={ROUTES.CHAT} replace />} />
          
          {/* 認証不要ルート */}
          <Route path={ROUTES.LOGIN} element={<LoginPage />} />
          <Route path={ROUTES.REGISTER} element={<RegisterPage />} />
          
          {/* 認証必須ルート */}
          <Route
            path={ROUTES.CHAT}
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          
          <Route
            path={ROUTES.DOMAINS}
            element={
              <ProtectedRoute>
                <DomainsPage />
              </ProtectedRoute>
            }
          />
          
          {/* 会話履歴ルート（追加） */}
          <Route
            path={ROUTES.CONVERSATIONS}
            element={
              <ProtectedRoute>
                <ConversationsPage />
              </ProtectedRoute>
            }
          />
          
          {/* 404 */}
          <Route path="*" element={<Navigate to={ROUTES.HOME} replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;