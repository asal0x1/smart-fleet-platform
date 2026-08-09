export type Role = 'client' | 'driver' | 'admin';

export interface User {
  id: number;
  phone: string;
  role: Role;
  full_name: string;
  email?: string | null;
  avatar_url?: string | null;
  avatar?: string | null;
  is_verified: boolean;
  created_at?: string;
}

export interface Tariff {
  id: number;
  name: string;
  name_uz?: string;
  base_fare: string;
  per_km?: string;
  per_minute?: string;
  minimum_fare?: string;
  icon_url?: string | null;
}

export type OrderStatus =
  | 'pending'
  | 'accepted'
  | 'driver_arrived'
  | 'ongoing'
  | 'completed'
  | 'cancelled';

export type PaymentMethod = 'cash' | 'click' | 'payme';

export interface OrderDriverInfo {
  id: number;
  name: string;
  car: string;
  car_number: string;
  rating: number;
}

export interface Order {
  id: number;
  client_name?: string;
  status: OrderStatus;
  from_address: string;
  from_lat: number;
  from_lng: number;
  to_address: string;
  to_lat: number;
  to_lng: number;
  tariff_name?: string;
  estimated_price?: string | number;
  final_price?: string | number;
  distance_km?: string | number;
  duration_min?: string | number;
  payment_method: PaymentMethod;
  payment_status?: string;
  driver?: OrderDriverInfo | null;
  created_at: string;
  accepted_at?: string | null;
  completed_at?: string | null;
}

export interface DriverProfile {
  id: number;
  full_name?: string;
  phone?: string;
  is_active: boolean;
  is_online: boolean;
  rating: string | number;
  total_trips: number;
  car_model?: string;
  car_color?: string;
  car_number?: string;
  license_number?: string;
  current_lat?: number | null;
  current_lng?: number | null;
  license_photo?: string | null;
  tech_passport_photo?: string | null;
  passport_photo?: string | null;
  car_photo?: string | null;
  missing_documents?: string[];
  documents_complete?: boolean;
}

export interface DriverDocuments {
  license_photo?: string | null;
  tech_passport_photo?: string | null;
  passport_photo?: string | null;
  car_photo?: string | null;
  missing_documents?: string[];
  is_complete?: boolean;
}

export interface AppNotification {
  id: number;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
  data?: Record<string, unknown>;
}

export interface HeavyEquipmentItem {
  name: string;
  quantity: number;
}

export type HeavyCategory = 'earth' | 'lift' | 'road' | 'loader';

export interface WeddingRequestPayload {
  car_brand: string;
  car_count: number;
  decoration_type?: 'flowers' | 'balloons' | 'ribbons';
  address: string;
  date: string;
  time?: string;
  duration_hours: number;
  contact_name: string;
  contact_phone: string;
  notes?: string;
}

export interface HeavyEquipmentRequestPayload {
  category: HeavyCategory;
  items: HeavyEquipmentItem[];
  address: string;
  lat?: number;
  lng?: number;
  start_date: string;
  start_time?: string;
  duration_days: number;
  contact_name: string;
  contact_phone: string;
  notes?: string;
}

export type RequestStatus = 'pending' | 'contacted' | 'confirmed' | 'completed' | 'cancelled';

export interface WeddingRequestItem {
  id: number;
  car_brand: string;
  car_count: number;
  decoration_type?: string;
  address: string;
  date: string;
  time?: string | null;
  duration_hours: number;
  estimated_price?: number | null;
  status: RequestStatus;
  created_at: string;
}

export interface HeavyEquipmentRequestItem {
  id: number;
  category: HeavyCategory;
  items: HeavyEquipmentItem[];
  address: string;
  start_date: string;
  start_time?: string | null;
  duration_days: number;
  estimated_price?: number | null;
  status: RequestStatus;
  created_at: string;
}

export type DriverExperience = '1-3' | '3-5' | '5-10' | '10+';
export type ContractDuration = '1_day' | '1_week' | '1_month' | '3_months' | '6_months' | '1_year';

export interface PersonalDriverRequestPayload {
  car_brand: string;
  driver_experience: DriverExperience;
  contract_duration: ContractDuration;
  address: string;
  start_date: string;
  contact_name: string;
  contact_phone: string;
  notes?: string;
}

export interface PersonalDriverRequestItem {
  id: number;
  car_brand: string;
  driver_experience: DriverExperience;
  contract_duration: ContractDuration;
  address: string;
  start_date: string;
  estimated_price?: number | null;
  status: RequestStatus;
  created_at: string;
}

export type BusCategory = 'wedding' | 'memorial' | 'tour';

export interface BusRequestPayload {
  category: BusCategory;
  bus_brand: string;
  bus_count: number;
  address: string;
  date: string;
  time?: string;
  duration_hours: number;
  contact_name: string;
  contact_phone: string;
  notes?: string;
}

export interface BusRequestItem {
  id: number;
  category: BusCategory;
  bus_brand: string;
  bus_count: number;
  address: string;
  date: string;
  time?: string | null;
  duration_hours: number;
  estimated_price?: number | null;
  status: RequestStatus;
  created_at: string;
}

export type GiftMemorialKind = 'gift' | 'memorial';

export interface GiftMemorialRequestPayload {
  kind: GiftMemorialKind;
  decoration_type?: 'flowers' | 'balloons' | 'ribbons';
  address: string;
  date: string;
  time?: string;
  contact_name: string;
  contact_phone: string;
  notes?: string;
}

export interface GiftMemorialRequestItem {
  id: number;
  kind: GiftMemorialKind;
  decoration_type?: string;
  address: string;
  date: string;
  time?: string | null;
  estimated_price?: number | null;
  status: RequestStatus;
  created_at: string;
}
