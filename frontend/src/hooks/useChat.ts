import { useState, useEffect, useRef, useCallback } from 'react';
import { Message } from '../types';
import { storage } from '../utils/storage';
import { WS_BASE_URL } from '../utils/constants';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [updateTrigger, setUpdateTrigger] = useState(0);
  
  const wsRef = useRef<WebSocket | null>(null);
  const messagesRef = useRef<Message[]>([]);
  const currentMessageRef = useRef<string>('');
  const currentMessageIdRef = useRef<string>('');

  const updateMessages = useCallback((newMessages: Message[]) => {
    messagesRef.current = newMessages;
    setMessages([...newMessages]);
    setUpdateTrigger(prev => prev + 1);
  }, []);

  useEffect(() => {
    // WebSocket接続（認証トークン付き）
    const token = storage.getAccessToken();
    
    if (!token) {
      console.error('No access token available');
      return;
    }

    const wsUrl = `${WS_BASE_URL}/ws/chat?token=${token}`;
    
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
          lastMessage.content = currentMessageRef.current;
          updateMessages(currentMessages);
        } else {
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
    
    if (ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      return;
    }

    console.log('Sending message:', text);

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date()
    };
    
    updateMessages([...messagesRef.current, userMessage]);
    
    setIsStreaming(true);
    currentMessageRef.current = '';
    currentMessageIdRef.current = '';

    ws.send(JSON.stringify({ message: text }));
  }, [isStreaming, updateMessages]);

  return {
    messages,
    sendMessage,
    isStreaming
  };
};