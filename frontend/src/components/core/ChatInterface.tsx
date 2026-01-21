import { FC, useState, useEffect } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { MessageList } from './MessageList';
import { InputBox } from './InputBox';
import { useDomainConfig } from '../../hooks/useDomainConfig';
import { useChat } from '../../hooks/useChat';
import './ChatInterface.css';

export const ChatInterface: FC = () => {
  const { domainConfig, loading: configLoading } = useDomainConfig();
  const { messages, sendMessage, isStreaming } = useChat();
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth >= 1024);

  useEffect(() => {
    const handleResize = () => {
      setSidebarOpen(window.innerWidth >= 1024);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // デバッグ用ログ
  useEffect(() => {
    console.log('Messages updated:', messages.length);
  }, [messages]);

  if (configLoading || !domainConfig) {
    return (
      <div className="loading-container">
        <div className="spinner">Loading...</div>
      </div>
    );
  }

  return (
    <div className="chat-interface">
      <Header 
        appName={domainConfig.domain.name}
        appDescription={domainConfig.domain.description}
        onMenuClick={() => setSidebarOpen(!sidebarOpen)}
      />
      
      <div className="main-content">
        {sidebarOpen && (
          <Sidebar
            quickActions={domainConfig.ui.quick_actions}
            sampleQueries={domainConfig.ui.sample_queries}
            onActionClick={sendMessage}
          />
        )}
        
        <div className="chat-area">
          <MessageList messages={messages} isStreaming={isStreaming} />
          
          <InputBox
            onSend={sendMessage}
            disabled={isStreaming}
            placeholder="メッセージを入力..."
            sampleQueries={domainConfig.ui.sample_queries}
          />
        </div>
      </div>
    </div>
  );
};