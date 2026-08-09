import { PickedLocation } from '../components/LocationPicker';

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
};

export type ClientStackParamList = {
  ClientTabs: undefined;
  TaxiOrder: undefined;
  TaxiTracking: { orderId: number };
  WeddingRequest: undefined;
  HeavyEquipment: undefined;
  PersonalDriver: undefined;
  BusBooking: undefined;
  GiftMemorial: undefined;
  ComingSoon: { title: string; icon: string; description: string };
  Notifications: undefined;
  ChangePassword: undefined;
};

export type ClientTabParamList = {
  Home: undefined;
  Orders: undefined;
  Wallet: undefined;
  Profile: undefined;
};

export type DriverStackParamList = {
  DriverTabs: undefined;
  Notifications: undefined;
  ChangePassword: undefined;
};

export type DriverTabParamList = {
  DriverHome: undefined;
  Trip: undefined;
  Earnings: undefined;
  DriverProfile: undefined;
};

export type { PickedLocation };
