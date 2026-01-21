import { FC, useRef, useEffect } from 'react';
import { Message } from '../../types';
import { MessageItem } from './MessageItem';
import './MessageList.css';

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
}

export const MessageList: FC<MessageListProps> = ({ messages, isStreaming }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // デバッグログ
  useEffect(() => {
    console.log('MessageList render:', {
      messageCount: messages.length,
      messages: messages.map(m => ({
        id: m.id,
        role: m.role,
        contentLength: m.content.length
      }))
    });
  }, [messages]);

  return (
    <div className="message-list">
      {messages.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">💬</div>
          <h2>メッセージを送信して分析を開始</h2>
          <p>サイドバーのクイックアクションまたはサンプルクエリをお試しください</p>
        </div>
      )}
      
      {messages.map((message) => {
        console.log('Rendering message:', message.id, message.role, message.content.substring(0, 50));
        return <MessageItem key={message.id} message={message} />;
      })}
      
      {isStreaming && (
        <div className="streaming-indicator">
          <div className="streaming-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span className="streaming-text">分析中...</span>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
};