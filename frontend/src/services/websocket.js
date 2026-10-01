class WebSocketClient {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
    this.reconnectTimer = null;
    this.isConnected = false;
    this.currentRoom = 'global';
  }

  connect(room = 'global') {
    this.currentRoom = room;
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      return;
    }

    let wsUrl;
    if (import.meta.env?.VITE_WS_URL) {
      const baseWs = import.meta.env.VITE_WS_URL.replace(/\/$/, '');
      wsUrl = `${baseWs}/ws/${room}`;
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      wsUrl = `${protocol}//${window.location.host}/ws/${room}`;
    }

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        this.isConnected = true;
        this.emit('connection_status', { connected: true, room });
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data && data.type) {
            this.emit(data.type, data);
            this.emit('*', data); // Wildcard listener
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.socket.onclose = () => {
        this.isConnected = false;
        this.emit('connection_status', { connected: false });
        this.scheduleReconnect();
      };

      this.socket.onerror = (err) => {
        this.emit('error', err);
      };
    } catch (e) {
      console.warn('WebSocket connection attempt failed:', e);
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect(this.currentRoom);
    }, 3000);
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType).add(callback);
    return () => this.off(eventType, callback);
  }

  off(eventType, callback) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).delete(callback);
    }
  }

  emit(eventType, data) {
    if (this.listeners.has(eventType)) {
      this.listeners.get(eventType).forEach((cb) => {
        try {
          cb(data);
        } catch (err) {
          console.error(`Error in WebSocket listener for ${eventType}:`, err);
        }
      });
    }
  }

  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.isConnected = false;
  }
}

export const wsClient = new WebSocketClient();
export default wsClient;
