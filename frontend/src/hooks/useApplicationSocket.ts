/**
 * useApplicationSocket — React hook for real-time agent event streaming via WebSocket.
 * Connects to ws://localhost:8000/ws/applications/{sessionId}
 */
import { useEffect, useRef, useCallback } from 'react';
import { useApplicationStore } from '../stores/applicationStore';

export type AgentEventType =
  | 'agent_message'
  | 'jobs_found'
  | 'fields_extracted'
  | 'mapping_complete'
  | 'questions_ready'
  | 'form_filled'
  | 'manual_action_required'
  | 'validation_error'
  | 'review_ready'
  | 'session_complete'
  | 'browser_opened'
  | 'error'
  | 'ping';

export interface AgentEvent {
  type: AgentEventType;
  node?: string;
  text?: string;
  count?: number;
  ready?: number;
  missing?: number;
  ambiguous?: number;
  field?: string;
  value?: string;
  reason?: string;
  instructions?: string;
  summary?: Record<string, unknown>;
  message?: string;
  recoverable?: boolean;
  url?: string;
}

interface UseApplicationSocketOptions {
  sessionId: string;
  accessToken: string;
  onEvent?: (event: AgentEvent) => void;
  enabled?: boolean;
}

export function useApplicationSocket({
  sessionId,
  accessToken,
  onEvent,
  enabled = true,
}: UseApplicationSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const addMessage = useApplicationStore(s => s.addMessage);
  const setStatus = useApplicationStore(s => s.setStatus);

  const connect = useCallback(() => {
    if (!enabled || !sessionId || !accessToken) return;

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.hostname}:8000/ws/applications/${sessionId}?token=${accessToken}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WS] Connected to session:', sessionId);
      };

      ws.onmessage = (event) => {
        try {
          const data: AgentEvent = JSON.parse(event.data);
          if (data.type === 'ping') return;

          // Push to store
          if (data.text) {
            addMessage({
              id: crypto.randomUUID(),
              type: data.type,
              text: data.text,
              node: data.node,
              timestamp: new Date().toISOString(),
              data: data,
            });
          }

          // Update status from specific event types
          if (data.type === 'review_ready') setStatus('reviewing');
          if (data.type === 'session_complete') setStatus('complete');
          if (data.type === 'manual_action_required') setStatus('paused');

          // Invoke caller callback
          onEvent?.(data);
        } catch (e) {
          console.error('[WS] Parse error:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Error:', error);
      };

      ws.onclose = (event) => {
        console.log('[WS] Closed:', event.code);
        wsRef.current = null;
        // Reconnect after 3s unless deliberately closed
        if (event.code !== 1000 && enabled) {
          reconnectTimerRef.current = setTimeout(connect, 3000);
        }
      };
    } catch (e) {
      console.error('[WS] Could not connect:', e);
    }
  }, [sessionId, accessToken, enabled, onEvent, addMessage, setStatus]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
    };
  }, [connect]);

  const sendMessage = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { sendMessage };
}
