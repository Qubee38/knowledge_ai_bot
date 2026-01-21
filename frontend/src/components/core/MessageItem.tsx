import { FC } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message } from '../../types';
import './MessageItem.css';

interface MessageItemProps {
  message: Message;
}

export const MessageItem: FC<MessageItemProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`message-item ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      
      <div className="message-content">
        <div className="message-header">
          <span className="message-role">
            {isUser ? 'You' : 'Assistant'}
          </span>
          <span className="message-time">
            {message.timestamp.toLocaleTimeString('ja-JP', {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </span>
        </div>
        
        <div className="message-body">
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // テーブルのカスタムスタイリング
                table: ({...props}) => (
                  <div className="markdown-table-wrapper">
                    <table className="markdown-table" {...props} />
                  </div>
                ),
                // コードブロック
                code: ({className, children, ...props}) => {
                  const match = /language-(\w+)/.exec(className || '');
                  return match ? (
                    <pre className="code-block">
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </pre>
                  ) : (
                    <code className="inline-code" {...props}>
                      {children}
                    </code>
                  );
                },
                // リンク
                a: ({...props}) => (
                  <a target="_blank" rel="noopener noreferrer" {...props} />
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
        
        {!isUser && (
          <div className="message-actions">
            <button className="message-action-btn" title="Good">👍</button>
            <button className="message-action-btn" title="Bad">👎</button>
            <button 
              className="message-action-btn" 
              title="Copy"
              onClick={() => {
                navigator.clipboard.writeText(message.content);
              }}
            >
              📋
            </button>
          </div>
        )}
      </div>
    </div>
  );
};