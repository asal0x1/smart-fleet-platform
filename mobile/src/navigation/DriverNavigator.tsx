import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { DriverStackParamList } from './types';
import { DriverTabNavigator } from './DriverTabNavigator';
import { NotificationsScreen } from '../screens/shared/NotificationsScreen';
import { ChangePasswordScreen } from '../screens/shared/ChangePasswordScreen';
import { NotificationSocketProvider } from '../context/NotificationSocketContext';

const Stack = createNativeStackNavigator<DriverStackParamList>();

export function DriverNavigator() {
  return (
    <NotificationSocketProvider>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="DriverTabs" component={DriverTabNavigator} />
        <Stack.Screen name="Notifications" component={NotificationsScreen} />
        <Stack.Screen name="ChangePassword" component={ChangePasswordScreen} />
      </Stack.Navigator>
    </NotificationSocketProvider>
  );
}
