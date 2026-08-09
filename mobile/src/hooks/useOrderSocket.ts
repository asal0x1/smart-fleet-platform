import { useEffect, useRef, useState } from 'react';
import { WS_BASE_URL } from '../api/config';
import { tokenStorage } from '../utils/storage';
import { OrderStatus } from '../types';

interface DriverLocation {
  lat: number;
  lng: number;
}

interface OrderSocketState {
  connected: boolean;
  driverLocation: DriverLocation | null;
  lastStatus: OrderStatus | null;
  lastEvent: string | null;
}

// Buyurtma real-vaqt kanaliga ulanadi: haydovchi joylashuvi va status
// o'zgarishlarini oladi. Backend `ws/orders/<id>/?token=<access>` orqali
// mijoz/haydovchi/adminga ruxsat beradi (apps/notifications/consumers.py).
export function useOrderSocket(orderId: number | null) {
  const [state, setState] = useState<OrderSocketState>({
    connected: false,
    driverLocation: null,
    lastStatus: null,
    lastEvent: null,
  });
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!orderId) return;
    let cancelled = false;
    let socket: WebSocket | null = null;

    (async () => {
      const token = await tokenStorage.getAccess();
      if (!token || cancelled) return;
      socket = new WebSocket(`${WS_BASE_URL}/orders/${orderId}/?token=${token}`);
      wsRef.current = socket;

      socket.onopen = () => setState((s) => ({ ...s, connected: true }));
      socket.onclose = () => setState((s) => ({ ...s, connected: false }));
      socket.onerror = () => setState((s) => ({ ...s, connected: false }));
      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'driver_location') {
            setState((s) => ({ ...s, driverLocation: { lat: msg.lat, lng: msg.lng } }));
          } else if (msg.type === 'order_event') {
            setState((s) => ({ ...s, lastStatus: msg.status, lastEvent: msg.event }));
          }
        } catch {
          // e'tiborsiz qoldiriladi
        }
      };
    })();

    return () => {
      cancelled = true;
      socket?.close();
      wsRef.current = null;
    };
  }, [orderId]);

  return state;
}
