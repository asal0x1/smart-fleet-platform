import { apiClient, ApiEnvelope } from './client';
import { DriverDocuments, DriverProfile } from '../types';
import { appendFileToFormData, multipartHeaders } from '../utils/uploadFile';

export async function getDriverProfile(): Promise<DriverProfile> {
  const res = await apiClient.get<ApiEnvelope<DriverProfile>>('/drivers/profile/');
  return res.data.data;
}

export async function updateDriverProfile(payload: {
  car_model?: string;
  car_color?: string;
  car_number?: string;
  license_number?: string;
}): Promise<DriverProfile> {
  const res = await apiClient.patch<ApiEnvelope<DriverProfile>>('/drivers/profile/', payload);
  return res.data.data;
}

export type DocumentField = 'license_photo' | 'tech_passport_photo' | 'passport_photo' | 'car_photo';

export async function uploadDriverDocument(field: DocumentField, uri: string): Promise<DriverDocuments> {
  const form = new FormData();
  await appendFileToFormData(form, field, uri);
  const res = await apiClient.post<ApiEnvelope<DriverDocuments>>('/drivers/documents/', form, {
    headers: multipartHeaders(),
  });
  return res.data.data;
}

export async function updateDriverLocation(lat: number, lng: number, accuracy?: number): Promise<void> {
  await apiClient.post('/drivers/location/', { lat, lng, accuracy });
}

export async function setDriverOnline(isOnline: boolean): Promise<{ is_online: boolean }> {
  const res = await apiClient.post<ApiEnvelope<{ is_online: boolean }>>('/drivers/online/', { is_online: isOnline });
  return res.data.data;
}

export interface NearbyDriver {
  id: number;
  name: string;
  lat: number;
  lng: number;
  distance_m: number;
  eta_min: number;
  car: string;
  rating: number;
}

export async function getNearbyDrivers(lat: number, lng: number, radius = 5000, limit = 10): Promise<NearbyDriver[]> {
  const res = await apiClient.get<ApiEnvelope<{ drivers: NearbyDriver[] }>>('/drivers/nearby/', {
    params: { lat, lng, radius, limit },
  });
  return res.data.data.drivers;
}
