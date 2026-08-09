import { apiClient, ApiEnvelope } from './client';

export interface GeocodeResult {
  address: string;
  lat: number;
  lng: number;
}

// Diqqat: backendda YANDEX_MAPS_API_KEY sozlanmagan bo'lsa bu so'rovlar
// 404/502 qaytaradi — chaqiruvchi tomon har doim xaritadan qo'lda nuqta
// tanlash imkoniyatiga ega bo'lishi kerak (LocationPicker shunday qurilgan).
export async function searchAddress(query: string): Promise<GeocodeResult | null> {
  if (!query.trim()) return null;
  const res = await apiClient.get<ApiEnvelope<GeocodeResult>>('/geocode/', { params: { q: query } });
  return res.data.data;
}

export async function reverseGeocode(lat: number, lng: number): Promise<GeocodeResult | null> {
  const res = await apiClient.get<ApiEnvelope<GeocodeResult | null>>('/geocode/reverse/', { params: { lat, lng } });
  return res.data.data;
}
