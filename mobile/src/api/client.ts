import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL } from './config';
import { tokenStorage } from '../utils/storage';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

let onUnauthorized: (() => void) | null = null;
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler;
}

apiClient.interceptors.request.use(async (config) => {
  const access = await tokenStorage.getAccess();
  if (access) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

// Boshqa modullar (masalan WebSocket qayta ulanish) ham shu funksiyani
// chaqirsa, bitta umumiy refreshPromise orqali parallel so'rovlar
// bitta refresh chaqiruviga birlashtiriladi.
export async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = doRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

async function doRefresh(): Promise<string | null> {
  const refresh = await tokenStorage.getRefresh();
  if (!refresh) return null;
  try {
    // Diqqat: refresh endpoint standart SimpleJWT formatida javob beradi
    // ({access: ...}), success/data o'ramasi bo'lmaydi.
    const res = await axios.post(`${API_BASE_URL}/auth/refresh/`, { refresh });
    const access = res.data?.access as string | undefined;
    if (!access) return null;
    await tokenStorage.setAccess(access);
    return access;
  } catch {
    return null;
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    if (error.response?.status === 401 && original && !original._retry && !original.url?.includes('/auth/refresh/')) {
      original._retry = true;

      const newAccess = await refreshAccessToken();

      if (newAccess) {
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${newAccess}`;
        return apiClient(original);
      }

      await tokenStorage.clear();
      onUnauthorized?.();
    }

    return Promise.reject(error);
  }
);

export interface ApiEnvelope<T> {
  success: boolean;
  message?: string;
  data: T;
  errors?: Record<string, string[]>;
}

export function extractErrorMessage(error: unknown, fallback = 'Xatolik yuz berdi'): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { message?: string; errors?: Record<string, string[]> } | undefined;
    if (data?.errors) {
      const first = Object.values(data.errors)[0];
      if (Array.isArray(first) && first.length) return first[0];
    }
    if (data?.message) return data.message;
    if (error.message === 'Network Error') {
      return 'Serverga ulanib bo\'lmadi. Backend ishga tushganini va telefon bilan bir xil Wi-Fi tarmog\'ida ekanini tekshiring.';
    }
  }
  return fallback;
}
