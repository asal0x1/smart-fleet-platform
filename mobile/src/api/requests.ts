import { apiClient, ApiEnvelope } from './client';
import {
  BusRequestItem,
  BusRequestPayload,
  GiftMemorialRequestItem,
  GiftMemorialRequestPayload,
  HeavyEquipmentRequestItem,
  HeavyEquipmentRequestPayload,
  PersonalDriverRequestItem,
  PersonalDriverRequestPayload,
  WeddingRequestItem,
  WeddingRequestPayload,
} from '../types';

interface RequestSubmitResult {
  request_id: number;
  status: string;
  estimated_price: number;
  message: string;
}

export async function submitWeddingRequest(payload: WeddingRequestPayload): Promise<RequestSubmitResult> {
  const res = await apiClient.post<ApiEnvelope<RequestSubmitResult>>('/wedding/requests/', payload);
  return res.data.data;
}

export async function submitHeavyEquipmentRequest(payload: HeavyEquipmentRequestPayload): Promise<RequestSubmitResult> {
  const res = await apiClient.post<ApiEnvelope<RequestSubmitResult>>('/heavy-equipment/requests/', payload);
  return res.data.data;
}

export async function getMyWeddingRequests(): Promise<WeddingRequestItem[]> {
  const res = await apiClient.get<ApiEnvelope<WeddingRequestItem[]>>('/wedding/requests/mine/');
  return res.data.data;
}

export async function getMyHeavyEquipmentRequests(): Promise<HeavyEquipmentRequestItem[]> {
  const res = await apiClient.get<ApiEnvelope<HeavyEquipmentRequestItem[]>>('/heavy-equipment/requests/mine/');
  return res.data.data;
}

export async function submitPersonalDriverRequest(payload: PersonalDriverRequestPayload): Promise<RequestSubmitResult> {
  const res = await apiClient.post<ApiEnvelope<RequestSubmitResult>>('/personal-driver/requests/', payload);
  return res.data.data;
}

export async function getMyPersonalDriverRequests(): Promise<PersonalDriverRequestItem[]> {
  const res = await apiClient.get<ApiEnvelope<PersonalDriverRequestItem[]>>('/personal-driver/requests/mine/');
  return res.data.data;
}

export async function submitBusRequest(payload: BusRequestPayload): Promise<RequestSubmitResult> {
  const res = await apiClient.post<ApiEnvelope<RequestSubmitResult>>('/bus/requests/', payload);
  return res.data.data;
}

export async function getMyBusRequests(): Promise<BusRequestItem[]> {
  const res = await apiClient.get<ApiEnvelope<BusRequestItem[]>>('/bus/requests/mine/');
  return res.data.data;
}

export async function submitGiftMemorialRequest(payload: GiftMemorialRequestPayload): Promise<RequestSubmitResult> {
  const res = await apiClient.post<ApiEnvelope<RequestSubmitResult>>('/gift-memorial/requests/', payload);
  return res.data.data;
}

export async function getMyGiftMemorialRequests(): Promise<GiftMemorialRequestItem[]> {
  const res = await apiClient.get<ApiEnvelope<GiftMemorialRequestItem[]>>('/gift-memorial/requests/mine/');
  return res.data.data;
}
