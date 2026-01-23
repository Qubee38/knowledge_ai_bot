import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Message } from '../types';
import { storage } from '../utils/storage';
import { WS_BASE_URL } from '../utils/constants';
import { conversationsService } from '../services/conversations.service';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [updateTrigger, setUpdateTrigger] = useState(0);
  
  const [searchParams] = useSearchParams();
  
  const wsRef = useRef<WebSocket | null>(null);
  const messagesRef = useRef<Message[]>([]);
  const currentMessageRef = useRef<string>('');
  const currentMessageIdRef = useRef<string>('');

  const updateMessages = useCallback((newMessages: Message[]) => {
    messagesRef.current = newMessages;
    setMessages([...newMessages]);
    setUpdateTrigger(prev => prev + 1);
  }, []);

  // 会話ID取得・会話作成
  useEffect(() => {
    const initConversation = async () => {
      // URLから会話ID取得
      const conversationIdFromUrl = searchParams.get('conversation');
      
      if (conversationIdFromUrl) {
        // 既存会話を読み込み
        setConversationId(conversationIdFromUrl);
        
        try {
          const conversation = await conversationsService.getConversation(
            conversationIdFromUrl
          );
          
          // 過去メッセージを復元
          const pastMessages: Message[] = conversation.messages.map(m => ({
            id: m.message_id,
            role: m.role,
            content: m.content,
            timestamp: new Date(m.created_at),
          }));
          
          updateMessages(pastMessages);
          
          console.log(`Loaded conversation: ${conversationIdFromUrl}, messages: ${pastMessages.length}`);
        } catch (error) {
          console.error('Failed to load conversation:', error);
        }
      } else {
        // 新規会話を作成
        try {
          const newConversation = await conversationsService.createConversation({
            domain: 'horse-racing', // TODO: ドメインを動的に取得
            title: '新しい会話',
          });
          
          setConversationId(newConversation.conversation_id);
          
          console.log(`Created new conversation: ${newConversation.conversation_id}`);
        } catch (error) {
          console.error('Failed to create conversation:', error);
        }
      }
    };

    initConversation();
  }, [searchParams]);

  // WebSocket接続
  useEffect(() => {
    if (!conversationId) {
      console.log('Waiting for conversation_id...');
      return;
    }

    const token = storage.getAccessToken();
    
    if (!token) {
      console.error('No access token available');
      return;
    }

    // WebSocket URL with conversation_id
    const wsUrl = `${WS_BASE_URL}/ws/chat?token=${token}&conversation_id=${conversationId}`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected successfully');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message:', data.type);

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
  }, [conversationId, updateMessages]);

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
    isStreaming,
    conversationId,
  };
};