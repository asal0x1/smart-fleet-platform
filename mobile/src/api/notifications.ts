import { apiClient, ApiEnvelope } from './client';
import { AppNotification } from '../types';

interface NotificationsPage {
  count: number;
  total_pages: number;
  current_page: number;
  next: string | null;
  previous: string | null;
  results: AppNotification[];
  unread: number;
}

export async function getNotifications(isRead?: boolean): Promise<{ results: AppNotification[]; unread: number }> {
  const res = await apiClient.get<ApiEnvelope<NotificationsPage>>('/notifications/', {
    params: isRead !== undefined ? { is_read: isRead } : undefined,
  });
  return { results: res.data.data.results, unread: res.data.data.unread };
}

export async function markNotificationRead(id: number): Promise<void> {
  await apiClient.patch(`/notifications/${id}/read/`);
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiClient.patch('/notifications/read-all/');
}
