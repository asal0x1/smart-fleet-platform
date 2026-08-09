import { apiClient, ApiEnvelope } from './client';
import { PaymentMethod } from '../types';

export interface CreatePaymentResult {
  payment_id: number;
  click_url?: string;
  amount: number;
  status: string;
}

export async function createPayment(orderId: number, method: PaymentMethod): Promise<CreatePaymentResult> {
  const res = await apiClient.post<ApiEnvelope<CreatePaymentResult>>('/payments/create/', {
    order_id: orderId,
    method,
  });
  return res.data.data;
}

export async function confirmCashPayment(paymentId: number): Promise<{ payment_id: number; status: string }> {
  const res = await apiClient.patch<ApiEnvelope<{ payment_id: number; status: string }>>(
    `/payments/${paymentId}/confirm-cash/`
  );
  return res.data.data;
}
