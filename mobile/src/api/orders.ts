import { apiClient, ApiEnvelope } from './client';
import { Order, OrderStatus, PaymentMethod, Tariff } from '../types';

export async function getTariffs(): Promise<Tariff[]> {
  const res = await apiClient.get<ApiEnvelope<Tariff[]>>('/orders/tariffs/');
  return res.data.data;
}

export interface EstimateResult {
  estimated_price: number;
  distance_km: number;
  duration_min: number;
}

export async function estimateOrder(payload: {
  from_lat: number;
  from_lng: number;
  to_lat: number;
  to_lng: number;
  tariff_id: number;
}): Promise<EstimateResult> {
  const res = await apiClient.post<ApiEnvelope<EstimateResult>>('/orders/estimate/', payload);
  return res.data.data;
}

export async function createOrder(payload: {
  from_address: string;
  from_lat: number;
  from_lng: number;
  to_address: string;
  to_lat: number;
  to_lng: number;
  tariff_id: number;
  payment_method: PaymentMethod;
}): Promise<Order> {
  const res = await apiClient.post<ApiEnvelope<Order>>('/orders/', payload);
  return res.data.data;
}

export async function getOrders(status?: string, limit?: number): Promise<Order[]> {
  const params: Record<string, string | number> = {};
  if (status) params.status = status;
  if (limit) params.limit = limit;
  const res = await apiClient.get<ApiEnvelope<Order[]>>('/orders/', {
    params: Object.keys(params).length ? params : undefined,
  });
  return res.data.data;
}

export async function getOrder(id: number): Promise<Order> {
  const res = await apiClient.get<ApiEnvelope<Order>>(`/orders/${id}/`);
  return res.data.data;
}

export async function getAvailableOrders(radius?: number): Promise<Order[]> {
  const res = await apiClient.get<ApiEnvelope<Order[]>>('/orders/available/', {
    params: radius ? { radius } : undefined,
  });
  return res.data.data;
}

export async function changeOrderStatus(
  id: number,
  status: OrderStatus,
  actualDistanceKm?: number
): Promise<Order> {
  const res = await apiClient.patch<ApiEnvelope<Order>>(`/orders/${id}/status/`, {
    status,
    ...(actualDistanceKm !== undefined ? { actual_distance_km: actualDistanceKm } : {}),
  });
  return res.data.data;
}

export interface Review {
  id: number;
  order: number;
  author_name: string;
  kind: string;
  rating: number;
  comment: string;
  created_at: string;
}

export async function getOrderReviews(orderId: number): Promise<Review[]> {
  const res = await apiClient.get<ApiEnvelope<Review[]>>(`/orders/${orderId}/review/`);
  return res.data.data;
}

export async function submitOrderReview(orderId: number, rating: number, comment?: string): Promise<Review> {
  const res = await apiClient.post<ApiEnvelope<Review>>(`/orders/${orderId}/review/`, { rating, comment });
  return res.data.data;
}
