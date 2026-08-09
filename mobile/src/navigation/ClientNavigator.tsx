import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ClientStackParamList } from './types';
import { ClientTabNavigator } from './ClientTabNavigator';
import { TaxiOrderScreen } from '../screens/client/TaxiOrderScreen';
import { TaxiTrackingScreen } from '../screens/client/TaxiTrackingScreen';
import { WeddingRequestScreen } from '../screens/client/WeddingRequestScreen';
import { HeavyEquipmentScreen } from '../screens/client/HeavyEquipmentScreen';
import { PersonalDriverScreen } from '../screens/client/PersonalDriverScreen';
import { BusBookingScreen } from '../screens/client/BusBookingScreen';
import { GiftMemorialScreen } from '../screens/client/GiftMemorialScreen';
import { ComingSoonScreen } from '../screens/client/ComingSoonScreen';
import { NotificationsScreen } from '../screens/shared/NotificationsScreen';
import { ChangePasswordScreen } from '../screens/shared/ChangePasswordScreen';
import { NotificationSocketProvider } from '../context/NotificationSocketContext';

const Stack = createNativeStackNavigator<ClientStackParamList>();

export function ClientNavigator() {
  return (
    <NotificationSocketProvider>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="ClientTabs" component={ClientTabNavigator} />
        <Stack.Screen name="TaxiOrder" component={TaxiOrderScreen} />
        <Stack.Screen name="TaxiTracking" component={TaxiTrackingScreen} />
        <Stack.Screen name="WeddingRequest" component={WeddingRequestScreen} />
        <Stack.Screen name="HeavyEquipment" component={HeavyEquipmentScreen} />
        <Stack.Screen name="PersonalDriver" component={PersonalDriverScreen} />
        <Stack.Screen name="BusBooking" component={BusBookingScreen} />
        <Stack.Screen name="GiftMemorial" component={GiftMemorialScreen} />
        <Stack.Screen name="ComingSoon" component={ComingSoonScreen} />
        <Stack.Screen name="Notifications" component={NotificationsScreen} />
        <Stack.Screen name="ChangePassword" component={ChangePasswordScreen} />
      </Stack.Navigator>
    </NotificationSocketProvider>
  );
}
