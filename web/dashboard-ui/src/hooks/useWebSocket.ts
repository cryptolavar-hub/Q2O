import { useState, useEffect, useCallback, useRef } from 'react';
import type { DashboardState, WebSocketMessage } from '../types/dashboard';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/dashboard';
const RECONNECT_INTERVAL = 3000; // 3 seconds

export function useWebSocket() {
  const [state, setState] = useState<DashboardState | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    try {
      console.log('Connecting to WebSocket:', WS_URL);
      const ws = new WebSocket(WS_URL);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('WebSocket message:', message.type);

          if (message.type === 'initial_state') {
            setState(message.data);
          } else if (message.type === 'task_update') {
            setState(prev => {
              if (!prev) return prev;
              const tasks = prev.tasks.map(task =>
                task.id === message.data.id ? { ...task, ...message.data } : task
              );
              return { ...prev, tasks };
            });
          } else if (message.type === 'agent_activity') {
            setState(prev => {
              if (!prev) return prev;
              const agents = prev.agents.map(agent =>
                agent.name === message.data.name ? { ...agent, ...message.data } : agent
              );
              return { ...prev, agents };
            });
          } else if (message.type === 'metric_update') {
            setState(prev => {
              if (!prev) return prev;
              return { ...prev, metrics: { ...prev.metrics, ...message.data } };
            });
          } else if (message.type === 'project_update') {
            setState(prev => {
              if (!prev) return prev;
              return { ...prev, project: { ...prev.project, ...message.data } };
            });
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error occurred');
        setConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected, will reconnect...');
        setConnected(false);
        wsRef.current = null;
        
        // Attempt reconnection after delay
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, RECONNECT_INTERVAL);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to connect');
      setConnected(false);
      
      // Attempt reconnection
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, RECONNECT_INTERVAL);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((type: string, data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, data }));
    }
  }, []);

  return {
    state,
    connected,
    error,
    sendMessage,
  };
}

