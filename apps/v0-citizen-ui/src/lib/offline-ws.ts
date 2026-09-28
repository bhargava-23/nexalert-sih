import { EventRecord } from "@/lib/nexalert-data";

type WsCallback = (event: EventRecord) => void;

class OfflineWebSocket {
  private socket: WebSocket | null = null;
  private url: string;
  private callbacks: Set<WsCallback> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private isConnected = false;

  constructor(url: string) {
    this.url = url;
  }

  connect() {
    if (this.socket?.readyState === WebSocket.OPEN) return;

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        console.log("[Offline WS] Connected to local emergency updates");
        this.isConnected = true;
        
        // Setup ping/pong
        setInterval(() => {
          if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket.send("ping");
          }
        }, 15000);
      };

      this.socket.onmessage = (event) => {
        try {
          if (event.data === "pong") return;
          const data = JSON.parse(event.data);
          
          if (data.type === "NEW_ALERT" && data.alert) {
            console.log("[Offline WS] Received new alert:", data.alert);
            // Transform to EventRecord format if needed
            const newEvent: EventRecord = {
              id: data.alert.alert_id,
              type: data.alert.headline,
              message: data.alert.description,
              level: data.alert.severity?.toLowerCase() === "extreme" ? "high" : 
                     data.alert.severity?.toLowerCase() === "severe" ? "high" : "medium",
              timestamp: new Date().toISOString(), // Use fresh timestamp
              isOffline: true // Mark as coming from offline local
            };
            
            this.notifyCallbacks(newEvent);
          }
        } catch (e) {
          console.error("[Offline WS] Failed to parse message:", e);
        }
      };

      this.socket.onclose = () => {
        this.isConnected = false;
        this.socket = null;
        this.scheduleReconnect();
      };
      
      this.socket.onerror = () => {
        this.isConnected = false;
        this.socket?.close();
      };
    } catch (e) {
      console.error("[Offline WS] Connection failed:", e);
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 5000);
  }

  subscribe(callback: WsCallback) {
    this.callbacks.add(callback);
    return () => this.callbacks.delete(callback);
  }

  private notifyCallbacks(event: EventRecord) {
    this.callbacks.forEach(cb => cb(event));
  }
}

// In local mode, backend is at the same origin or specific local IP
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsHost = import.meta.env.VITE_API_BASE_URL 
  ? new URL(import.meta.env.VITE_API_BASE_URL).host
  : window.location.host;
  
export const offlineWs = new OfflineWebSocket(`${wsProtocol}//${wsHost}/ws/emergency-updates`);
