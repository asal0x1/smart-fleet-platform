import { apiClient, ApiEnvelope } from './client';
import { Role, User } from '../types';
import { appendFileToFormData, multipartHeaders } from '../utils/uploadFile';

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: User;
}

export async function login(phone: string, password: string): Promise<LoginResponse> {
  const res = await apiClient.post<ApiEnvelope<LoginResponse>>('/auth/login/', { phone, password });
  return res.data.data;
}

export interface RegisterResponse {
  user_id: number;
  phone: string;
  role: Role;
  token: string;
}

export async function register(payload: {
  phone: string;
  password: string;
  role: Role;
  full_name?: string;
}): Promise<RegisterResponse> {
  const res = await apiClient.post<ApiEnvelope<RegisterResponse>>('/auth/register/', payload);
  return res.data.data;
}

export async function logout(refreshToken: string): Promise<void> {
  await apiClient.post('/auth/logout/', { refresh_token: refreshToken });
}

export async function sendOtp(phone: string): Promise<{ message_id: string; expires_in: number }> {
  const res = await apiClient.post<ApiEnvelope<{ message_id: string; expires_in: number }>>('/auth/send-otp/', { phone });
  return res.data.data;
}

export async function resetPassword(phone: string, otp: string, newPassword: string) {
  const res = await apiClient.post<ApiEnvelope<{ access_token: string; refresh_token: string }>>(
    '/auth/reset-password/',
    { phone, otp, new_password: newPassword }
  );
  return res.data.data;
}

export async function getProfile(): Promise<User> {
  const res = await apiClient.get<ApiEnvelope<User>>('/auth/profile/');
  return res.data.data;
}

export async function updateProfile(payload: Partial<Pick<User, 'full_name' | 'email' | 'avatar_url'>>): Promise<User> {
  const res = await apiClient.patch<ApiEnvelope<User>>('/auth/profile/', payload);
  return res.data.data;
}

export async function uploadAvatar(uri: string): Promise<User> {
  const form = new FormData();
  await appendFileToFormData(form, 'avatar', uri);
  const res = await apiClient.patch<ApiEnvelope<User>>('/auth/profile/', form, {
    headers: multipartHeaders(),
  });
  return res.data.data;
}

export async function changePassword(oldPassword: string, newPassword: string) {
  const res = await apiClient.post<ApiEnvelope<{ access_token: string; refresh_token: string }>>(
    '/auth/change-password/',
    { old_password: oldPassword, new_password: newPassword }
  );
  return res.data.data;
}
