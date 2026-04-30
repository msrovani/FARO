"use client";

import { useEffect, useRef, useState, useCallback } from "react";
// Using native browser notifications instead of react-hot-toast

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

interface WebSocketHookReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => void;
  error: string | null;
  reconnect: () => void;
}

export function useWebSocket(url: string): WebSocketHookReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    try {
      // Close existing connection if any
      if (ws.current) {
        ws.current.close();
      }

      // Create new WebSocket connection
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
        console.log("WebSocket connected");
        if (Notification.permission === "granted") {
          new Notification("F.A.R.O.", {
            body: "Conectado ao servidor em tempo real",
            icon: "/favicon.ico"
          });
        }
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          
          // Handle different message types
          handleWebSocketMessage(message);
        } catch (err) {
          console.error("Failed to parse WebSocket message:", err);
        }
      };

      ws.current.onclose = (event) => {
        setIsConnected(false);
        console.log("WebSocket disconnected:", event.code, event.reason);
        
        // Attempt reconnection if not explicitly closed
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectAttempts.current++;
          
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting to reconnect... (attempt ${reconnectAttempts.current})`);
            connect();
          }, delay);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setError("Falha ao reconectar após várias tentativas");
          if (Notification.permission === "granted") {
            new Notification("F.A.R.O. - Erro", {
              body: "Falha na conexão em tempo real",
              icon: "/favicon.ico"
            });
          }
        }
      };

      ws.current.onerror = (event) => {
        console.error("WebSocket error:", event);
        setError("Erro na conexão WebSocket");
        if (Notification.permission === "granted") {
          new Notification("F.A.R.O. - Erro", {
            body: "Erro na conexão em tempo real",
            icon: "/favicon.ico"
          });
        }
      };

    } catch (err) {
      console.error("Failed to create WebSocket connection:", err);
      setError("Falha ao criar conexão WebSocket");
    }
  }, [url]);

  const sendMessage = useCallback((message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify(message));
      } catch (err) {
        console.error("Failed to send WebSocket message:", err);
        setError("Falha ao enviar mensagem");
      }
    } else {
      setError("WebSocket não está conectado");
      if (Notification.permission === "granted") {
        new Notification("F.A.R.O. - Erro", {
          body: "Sem conexão com o servidor",
          icon: "/favicon.ico"
        });
      }
    }
  }, []);

  const reconnect = useCallback(() => {
    reconnectAttempts.current = 0;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    connect();
  }, [connect]);

  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case "new_observation":
        if (Notification.permission === "granted") {
          new Notification("F.A.R.O. - Nova Observação", {
            body: `Nova observação: ${message.data.plate_number}`,
            icon: "/favicon.ico"
          });
        }
        // Trigger refresh of queue
        window.dispatchEvent(new CustomEvent("refresh-queue"));
        break;

      case "alert_triggered":
        if (Notification.permission === "granted") {
          new Notification("F.A.R.O. - Alerta", {
            body: `Alerta: ${message.data.title}`,
            icon: "/favicon.ico"
          });
        }
        // Trigger refresh of alerts
        window.dispatchEvent(new CustomEvent("refresh-alerts"));
        break;

      case "agent_status_change":
        if (Notification.permission === "granted") {
          new Notification("F.A.R.O. - Status do Agente", {
            body: `Agente ${message.data.agent_name}: ${message.data.status}`,
            icon: "/favicon.ico"
          });
        }
        // Trigger refresh of agents
        window.dispatchEvent(new CustomEvent("refresh-agents"));
        break;

      case "system_alert":
        if (Notification.permission === "granted") {
          new Notification("F.A.R.O. - Alerta do Sistema", {
            body: message.data.message,
            icon: "/favicon.ico"
          });
        }
        break;

      case "suspicion_report_created":
        if (Notification.permission === "granted") {
          new Notification("F.A.R.O. - Relatório de Suspeição", {
            body: `Relatório de suspeição criado: ${message.data.plate_number}`,
            icon: "/favicon.ico"
          });
        }
        // Trigger refresh of suspicion reports
        window.dispatchEvent(new CustomEvent("refresh-suspicion-reports"));
        break;

      case "watchlist_match":
        if (Notification.permission === "granted") {
          new Notification("F.A.R.O. - Watchlist", {
            body: `Match na watchlist: ${message.data.plate_number}`,
            icon: "/favicon.ico"
          });
        }
        break;

      case "device_status_change":
        if (Notification.permission === "granted") {
          new Notification("F.A.R.O. - Dispositivo", {
            body: `Dispositivo ${message.data.device_id}: ${message.data.status}`,
            icon: "/favicon.ico"
          });
        }
        // Trigger refresh of devices
        window.dispatchEvent(new CustomEvent("refresh-devices"));
        break;

      default:
        console.log("Unknown WebSocket message type:", message.type);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws.current) {
        ws.current.close(1000, "Component unmounted");
      }
    };
  }, [connect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    error,
    reconnect,
  };
}

// Hook for real-time queue updates
export function useQueueWebSocket() {
  const { isConnected, lastMessage, sendMessage, error, reconnect } = useWebSocket(
    `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/ws/queue`
  );

  return {
    isConnected,
    lastMessage,
    sendMessage,
    error,
    reconnect,
  };
}

// Hook for real-time alerts
export function useAlertsWebSocket() {
  const { isConnected, lastMessage, sendMessage, error, reconnect } = useWebSocket(
    `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/ws/alerts`
  );

  return {
    isConnected,
    lastMessage,
    sendMessage,
    error,
    reconnect,
  };
}

// Hook for real-time monitoring
export function useMonitoringWebSocket() {
  const { isConnected, lastMessage, sendMessage, error, reconnect } = useWebSocket(
    `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/ws/monitoring`
  );

  return {
    isConnected,
    lastMessage,
    sendMessage,
    error,
    reconnect,
  };
}

// Hook for real-time agent tracking
export function useAgentsWebSocket() {
  const { isConnected, lastMessage, sendMessage, error, reconnect } = useWebSocket(
    `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/ws/agents`
  );

  return {
    isConnected,
    lastMessage,
    sendMessage,
    error,
    reconnect,
  };
}
