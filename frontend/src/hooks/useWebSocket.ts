import { useEffect, useState, useRef, useCallback } from 'react';
import { WebSocketEvent } from '../types/event';

export const useWebSocket = (url: string = '/api/v1/ws/events') => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null);
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;

    // Attach JWT token as query param for WebSocket authentication
    const token = localStorage.getItem('metroflow_token');
    const authSuffix = token ? `?token=${encodeURIComponent(token)}` : '';
    const wsUrl = `${protocol}//${host}${url}${authSuffix}`;

    const socket = new WebSocket(wsUrl);
    wsRef.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const parsed: WebSocketEvent = JSON.parse(event.data);
        setLastEvent(parsed);
        setEvents((prev) => [parsed, ...prev].slice(0, 50));
      } catch (e) {
        console.error('Failed to parse WebSocket event:', e);
      }
    };

    socket.onclose = (evt) => {
      setIsConnected(false);
      if (evt.code === 4001) {
        console.warn('WebSocket closed: authentication required (4001)');
      }
    };

    socket.onerror = (err) => {
      console.error('WebSocket error:', err);
      setIsConnected(false);
    };

    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, [url]);

  const sendMessage = useCallback((msg: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(msg);
    }
  }, []);

  return {
    isConnected,
    lastEvent,
    events,
    sendMessage,
  };
};
