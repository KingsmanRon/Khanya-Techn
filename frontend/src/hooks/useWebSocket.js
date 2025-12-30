/**
 * MTP WebSocket Hook
 * Real-time updates for audit events, trust scores, and alerts
 */
import { useState, useEffect, useCallback, useRef } from 'react';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

/**
 * WebSocket connection states
 */
export const ConnectionState = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  RECONNECTING: 'reconnecting',
  ERROR: 'error'
};

/**
 * Event types from the server
 */
export const EventType = {
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  ERROR: 'error',
  AUDIT_EVENT: 'audit_event',
  AUDIT_BATCH_ANCHORED: 'audit_batch_anchored',
  TRUST_SCORE_UPDATE: 'trust_score_update',
  TRUST_THRESHOLD_ALERT: 'trust_threshold_alert',
  AGENT_SUSPENDED: 'agent_suspended',
  AGENT_ACTIVATED: 'agent_activated',
  KILL_SWITCH_TRIGGERED: 'kill_switch_triggered',
  CERTIFICATION_GRANTED: 'certification_granted',
  CERTIFICATION_REVOKED: 'certification_revoked',
  DISPUTE_FILED: 'dispute_filed',
  DISPUTE_RESOLVED: 'dispute_resolved',
  SYSTEM_ALERT: 'system_alert',
  METRICS_UPDATE: 'metrics_update'
};

/**
 * Custom hook for WebSocket connection to MTP backend
 *
 * @param {Object} options - Configuration options
 * @param {string} options.userId - User ID for connection
 * @param {string} options.orgId - Organization ID for org-wide events
 * @param {boolean} options.autoConnect - Auto-connect on mount (default: true)
 * @param {number} options.reconnectAttempts - Max reconnection attempts (default: 5)
 * @param {number} options.reconnectInterval - Base reconnect interval in ms (default: 3000)
 * @returns {Object} WebSocket state and control functions
 */
export function useWebSocket({
  userId = null,
  orgId = null,
  autoConnect = true,
  reconnectAttempts = 5,
  reconnectInterval = 3000
} = {}) {
  const [connectionState, setConnectionState] = useState(ConnectionState.DISCONNECTED);
  const [lastMessage, setLastMessage] = useState(null);
  const [clientId, setClientId] = useState(null);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef(null);
  const eventHandlersRef = useRef(new Map());
  const pingIntervalRef = useRef(null);

  /**
   * Build WebSocket URL with query params
   */
  const buildUrl = useCallback(() => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (orgId) params.append('org_id', orgId);

    const queryString = params.toString();
    return `${WS_URL}/api/ws/connect${queryString ? `?${queryString}` : ''}`;
  }, [userId, orgId]);

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    setConnectionState(ConnectionState.CONNECTING);
    setError(null);

    try {
      const url = buildUrl();
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        setConnectionState(ConnectionState.CONNECTED);
        reconnectCountRef.current = 0;

        // Start ping interval for keep-alive
        pingIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ action: 'ping' }));
          }
        }, 30000); // Ping every 30 seconds
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);

          // Extract client ID from connected message
          if (data.type === EventType.CONNECTED && data.client_id) {
            setClientId(data.client_id);
          }

          // Call registered event handlers
          const handlers = eventHandlersRef.current.get(data.type) || [];
          handlers.forEach(handler => {
            try {
              handler(data);
            } catch (err) {
              console.error('Error in event handler:', err);
            }
          });

          // Call wildcard handlers (for all events)
          const wildcardHandlers = eventHandlersRef.current.get('*') || [];
          wildcardHandlers.forEach(handler => {
            try {
              handler(data);
            } catch (err) {
              console.error('Error in wildcard handler:', err);
            }
          });
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
        setConnectionState(ConnectionState.ERROR);
      };

      wsRef.current.onclose = (event) => {
        setConnectionState(ConnectionState.DISCONNECTED);
        clearInterval(pingIntervalRef.current);

        // Attempt to reconnect if not a clean close
        if (!event.wasClean && reconnectCountRef.current < reconnectAttempts) {
          setConnectionState(ConnectionState.RECONNECTING);
          const delay = reconnectInterval * Math.pow(2, reconnectCountRef.current);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectCountRef.current++;
            connect();
          }, delay);
        }
      };
    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError(err.message);
      setConnectionState(ConnectionState.ERROR);
    }
  }, [buildUrl, reconnectAttempts, reconnectInterval]);

  /**
   * Disconnect from WebSocket server
   */
  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimeoutRef.current);
    clearInterval(pingIntervalRef.current);
    reconnectCountRef.current = reconnectAttempts; // Prevent auto-reconnect

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setConnectionState(ConnectionState.DISCONNECTED);
    setClientId(null);
  }, [reconnectAttempts]);

  /**
   * Subscribe to updates for a specific agent
   */
  const subscribeToAgent = useCallback((mtpId) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        mtp_id: mtpId
      }));
    }
  }, []);

  /**
   * Subscribe to specific event types
   */
  const subscribeToEvents = useCallback((eventTypes) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        event_types: eventTypes
      }));
    }
  }, []);

  /**
   * Unsubscribe from agent updates
   */
  const unsubscribeFromAgent = useCallback((mtpId) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        mtp_id: mtpId
      }));
    }
  }, []);

  /**
   * Register an event handler
   * @param {string} eventType - Event type to listen for (or '*' for all)
   * @param {Function} handler - Handler function
   * @returns {Function} Unsubscribe function
   */
  const on = useCallback((eventType, handler) => {
    if (!eventHandlersRef.current.has(eventType)) {
      eventHandlersRef.current.set(eventType, []);
    }
    eventHandlersRef.current.get(eventType).push(handler);

    // Return unsubscribe function
    return () => {
      const handlers = eventHandlersRef.current.get(eventType);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }, []);

  /**
   * Remove all handlers for an event type
   */
  const off = useCallback((eventType) => {
    eventHandlersRef.current.delete(eventType);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    // State
    connectionState,
    isConnected: connectionState === ConnectionState.CONNECTED,
    lastMessage,
    clientId,
    error,

    // Actions
    connect,
    disconnect,
    subscribeToAgent,
    subscribeToEvents,
    unsubscribeFromAgent,
    on,
    off
  };
}

/**
 * Hook for subscribing to real-time audit events
 */
export function useAuditEvents(onEvent) {
  const { isConnected, on, subscribeToEvents } = useWebSocket();

  useEffect(() => {
    if (isConnected) {
      subscribeToEvents([EventType.AUDIT_EVENT, EventType.AUDIT_BATCH_ANCHORED]);
    }
  }, [isConnected, subscribeToEvents]);

  useEffect(() => {
    if (onEvent) {
      const unsubAudit = on(EventType.AUDIT_EVENT, onEvent);
      const unsubBatch = on(EventType.AUDIT_BATCH_ANCHORED, onEvent);

      return () => {
        unsubAudit();
        unsubBatch();
      };
    }
  }, [on, onEvent]);
}

/**
 * Hook for subscribing to trust score updates
 */
export function useTrustUpdates(onUpdate) {
  const { isConnected, on, subscribeToEvents } = useWebSocket();

  useEffect(() => {
    if (isConnected) {
      subscribeToEvents([EventType.TRUST_SCORE_UPDATE, EventType.TRUST_THRESHOLD_ALERT]);
    }
  }, [isConnected, subscribeToEvents]);

  useEffect(() => {
    if (onUpdate) {
      const unsubUpdate = on(EventType.TRUST_SCORE_UPDATE, onUpdate);
      const unsubAlert = on(EventType.TRUST_THRESHOLD_ALERT, onUpdate);

      return () => {
        unsubUpdate();
        unsubAlert();
      };
    }
  }, [on, onUpdate]);
}

/**
 * Hook for subscribing to kill switch events
 */
export function useKillSwitchAlerts(onAlert) {
  const { isConnected, on, subscribeToEvents } = useWebSocket();

  useEffect(() => {
    if (isConnected) {
      subscribeToEvents([
        EventType.KILL_SWITCH_TRIGGERED,
        EventType.AGENT_SUSPENDED,
        EventType.AGENT_ACTIVATED
      ]);
    }
  }, [isConnected, subscribeToEvents]);

  useEffect(() => {
    if (onAlert) {
      const unsub1 = on(EventType.KILL_SWITCH_TRIGGERED, onAlert);
      const unsub2 = on(EventType.AGENT_SUSPENDED, onAlert);
      const unsub3 = on(EventType.AGENT_ACTIVATED, onAlert);

      return () => {
        unsub1();
        unsub2();
        unsub3();
      };
    }
  }, [on, onAlert]);
}

export default useWebSocket;
