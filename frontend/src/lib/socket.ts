export type TelemetryCallback = (data: any) => void;

export class LiveSocketClient {
  private ws: WebSocket | null = null;
  private listeners: TelemetryCallback[] = [];
  private reconnectInterval: any = null;

  connect() {
    if (typeof window === "undefined") return;
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/live";
    
    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log("[MetroFlow WS] Connected to live telemetry feed.");
        if (this.reconnectInterval) {
          clearInterval(this.reconnectInterval);
          this.reconnectInterval = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          this.listeners.forEach((cb) => cb(parsed));
        } catch (e) {
          // ignore non-json messages
        }
      };

      this.ws.onclose = () => {
        console.log("[MetroFlow WS] Connection closed. Retrying in 5s...");
        this.scheduleReconnect();
      };

      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch (e) {
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (!this.reconnectInterval) {
      this.reconnectInterval = setInterval(() => {
        this.connect();
      }, 5000);
    }
  }

  subscribe(callback: TelemetryCallback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback);
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const socketClient = new LiveSocketClient();
