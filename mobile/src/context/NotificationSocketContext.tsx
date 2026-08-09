import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { WS_BASE_URL } from '../api/config';
import { tokenStorage } from '../utils/storage';
import { refreshAccessToken } from '../api/client';
import { presentLocalNotification } from '../utils/localNotifications';
import { useAuth } from './AuthContext';
import { useLanguage } from '../i18n/LanguageContext';

export interface NewOrderEvent {
  type: 'new_order';
  order_id: number;
  from_address: string;
  to_address: string;
  estimated_price: number;
  distance_km: number;
  tariff: string | null;
  created_at: string;
}

export interface PersonalNotificationEvent {
  type: 'notification';
  id: number | null;
  notification_type: string;
  title: string;
  body: string;
  payload: Record<string, unknown>;
}

type SocketEvent = NewOrderEvent | PersonalNotificationEvent;
type Listener = (event: SocketEvent) => void;

interface NotificationSocketValue {
  connected: boolean;
  unread: number;
  subscribe: (listener: Listener) => () => void;
}

const NotificationSocketContext = createContext<NotificationSocketValue>({
  connected: false,
  unread: 0,
  subscribe: () => () => {},
});

const BASE_RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_DELAY_MS = 60000;
// Server "unauthorized" deb yopgan close kodlari (apps/notifications/consumers.py)
const AUTH_CLOSE_CODES = [4401, 4403];

export function NotificationSocketProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const [connected, setConnected] = useState(false);
  const [unread, setUnread] = useState(0);
  const listenersRef = useRef<Set<Listener>>(new Set());
  const socketRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);

  useEffect(() => {
    let stopped = false;

    async function connect() {
      if (stopped || !isAuthenticated) return;
      const token = await tokenStorage.getAccess();
      if (!token || stopped) return;

      const socket = new WebSocket(`${WS_BASE_URL}/notifications/?token=${token}`);
      socketRef.current = socket;

      socket.onopen = () => {
        attemptRef.current = 0;
        setConnected(true);
        pingIntervalRef.current = setInterval(() => {
          socket.send(JSON.stringify({ action: 'ping' }));
        }, 30000);
      };

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'connected') {
            setUnread(msg.unread ?? 0);
          } else if (msg.type === 'notification') {
            setUnread((n) => n + 1);
            listenersRef.current.forEach((fn) => fn(msg));
            presentLocalNotification(msg.title, msg.body);
          } else if (msg.type === 'new_order') {
            listenersRef.current.forEach((fn) => fn(msg));
            presentLocalNotification(
              t('incomingOrder.title'),
              `${msg.from_address} → ${msg.to_address} (${Number(msg.estimated_price).toLocaleString('ru-RU')} ${t('common.somUnit')})`
            );
          }
        } catch {
          // e'tiborsiz qoldiriladi
        }
      };

      socket.onclose = (event) => {
        setConnected(false);
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        if (stopped || !isAuthenticated) return;

        // Token yaroqsiz bo'lgani uchun rad etilgan bo'lsa — eskirgan
        // token bilan cheksiz urinish o'rniga avval uni yangilashga
        // harakat qilamiz. Yangilab bo'lmasa (refresh token ham
        // yaroqsiz), foydalanuvchi qayta kirmaguncha urinishni to'xtatamiz
        // — aks holda serverni bo'sh so'rovlar bilan bombalab yuboramiz.
        if (AUTH_CLOSE_CODES.includes(event.code)) {
          refreshAccessToken().then((newToken) => {
            if (stopped) return;
            if (newToken) {
              reconnectTimeoutRef.current = setTimeout(connect, 500);
            }
            // newToken == null: sukut bilan to'xtaymiz, isAuthenticated
            // o'zgarganda (masalan qayta login) effekt qaytadan ishga tushadi
          });
          return;
        }

        const delay = Math.min(BASE_RECONNECT_DELAY_MS * 2 ** attemptRef.current, MAX_RECONNECT_DELAY_MS);
        attemptRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(connect, delay);
      };

      socket.onerror = () => socket.close();
    }

    if (isAuthenticated) {
      connect();
    }

    return () => {
      stopped = true;
      attemptRef.current = 0;
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      socketRef.current?.close();
      socketRef.current = null;
      setConnected(false);
    };
  }, [isAuthenticated]);

  const subscribe = (listener: Listener) => {
    listenersRef.current.add(listener);
    return () => listenersRef.current.delete(listener);
  };

  return (
    <NotificationSocketContext.Provider value={{ connected, unread, subscribe }}>
      {children}
    </NotificationSocketContext.Provider>
  );
}

export function useNotificationSocket() {
  return useContext(NotificationSocketContext);
}
