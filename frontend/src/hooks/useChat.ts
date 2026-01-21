import { useState, useEffect, useRef, useCallback } from 'react';
import { Message } from '../types';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [updateTrigger, setUpdateTrigger] = useState(0); // 強制更新用
  
  const wsRef = useRef<WebSocket | null>(null);
  const messagesRef = useRef<Message[]>([]); // 最新のメッセージを保持
  const currentMessageRef = useRef<string>('');
  const currentMessageIdRef = useRef<string>('');

  // メッセージ更新関数
  const updateMessages = useCallback((newMessages: Message[]) => {
    messagesRef.current = newMessages;
    setMessages([...newMessages]); // 新しい配列を作成して強制更新
    setUpdateTrigger(prev => prev + 1);
  }, []);

  useEffect(() => {
    // WebSocket接続
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = '8000';
    const wsUrl = `${protocol}//${host}:${port}/ws/chat`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected successfully');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data.type, data.content?.substring(0, 30));

      if (data.type === 'delta') {
        currentMessageRef.current += data.content;
        
        const currentMessages = [...messagesRef.current];
        const lastMessage = currentMessages[currentMessages.length - 1];
        
        if (lastMessage && lastMessage.id === currentMessageIdRef.current) {
          // 既存のアシスタントメッセージを更新
          lastMessage.content = currentMessageRef.current;
          updateMessages(currentMessages);
        } else {
          // 新しいアシスタントメッセージを追加
          const newMessageId = `assistant-${Date.now()}`;
          currentMessageIdRef.current = newMessageId;
          
          const newMessage: Message = {
            id: newMessageId,
            role: 'assistant',
            content: currentMessageRef.current,
            timestamp: new Date()
          };
          
          updateMessages([...currentMessages, newMessage]);
        }
      } else if (data.type === 'done') {
        console.log('Streaming completed');
        setIsStreaming(false);
        currentMessageRef.current = '';
        currentMessageIdRef.current = '';
      } else if (data.type === 'error') {
        console.error('Chat error:', data.message);
        setIsStreaming(false);
        currentMessageRef.current = '';
        currentMessageIdRef.current = '';
        
        // エラーメッセージを表示
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `❌ エラーが発生しました: ${data.message}`,
          timestamp: new Date()
        };
        updateMessages([...messagesRef.current, errorMessage]);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsStreaming(false);
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected', event.code, event.reason);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [updateMessages]);

  const sendMessage = useCallback((text: string) => {
    if (!text.trim() || !wsRef.current || isStreaming) {
      console.warn('Cannot send message:', { 
        hasText: !!text.trim(), 
        hasWs: !!wsRef.current, 
        isStreaming 
      });
      return;
    }

    const ws = wsRef.current;
    
    // 接続状態チェック
    if (ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      return;
    }

    console.log('Sending message:', text);

    // ユーザーメッセージ追加
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date()
    };
    
    updateMessages([...messagesRef.current, userMessage]);
    
    // ストリーミング開始
    setIsStreaming(true);
    currentMessageRef.current = '';
    currentMessageIdRef.current = '';

    // WebSocketで送信
    ws.send(JSON.stringify({ message: text }));
  }, [isStreaming, updateMessages]);

  return {
    messages,
    sendMessage,
    isStreaming
  };
};