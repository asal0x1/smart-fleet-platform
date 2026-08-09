import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { tokenStorage } from '../utils/storage';
import { setUnauthorizedHandler } from '../api/client';
import * as authApi from '../api/auth';
import { Role, User } from '../types';

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (phone: string, password: string) => Promise<void>;
  register: (phone: string, password: string, role: Role, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  setUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const bootstrap = useCallback(async () => {
    setIsLoading(true);
    try {
      const access = await tokenStorage.getAccess();
      if (!access) {
        setUser(null);
        return;
      }
      const profile = await authApi.getProfile();
      setUser(profile);
    } catch {
      await tokenStorage.clear();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null);
    });
    bootstrap();
  }, [bootstrap]);

  const login = useCallback(async (phone: string, password: string) => {
    const res = await authApi.login(phone, password);
    await tokenStorage.setTokens(res.access_token, res.refresh_token);
    setUser(res.user);
  }, []);

  const register = useCallback(async (phone: string, password: string, role: Role, fullName?: string) => {
    await authApi.register({ phone, password, role, full_name: fullName });
    // Register faqat access token beradi (refresh yo'q) — sessiya doimiy
    // saqlanishi uchun darhol login qilib to'liq token juftligini olamiz.
    const res = await authApi.login(phone, password);
    await tokenStorage.setTokens(res.access_token, res.refresh_token);
    setUser(res.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      const refresh = await tokenStorage.getRefresh();
      if (refresh) await authApi.logout(refresh);
    } catch {
      // tarmoq xatosi bo'lsa ham lokal seansni tozalaymiz
    } finally {
      await tokenStorage.clear();
      setUser(null);
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const profile = await authApi.getProfile();
    setUser(profile);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isLoading, isAuthenticated: !!user, login, register, logout, refreshUser, setUser }),
    [user, isLoading, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth AuthProvider ichida ishlatilishi kerak');
  return ctx;
}
