import React from 'react';
import { Text } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { DriverTabParamList } from './types';
import { DriverHomeScreen } from '../screens/driver/DriverHomeScreen';
import { TripScreen } from '../screens/driver/TripScreen';
import { EarningsScreen } from '../screens/driver/EarningsScreen';
import { DriverProfileScreen } from '../screens/driver/DriverProfileScreen';
import { colors } from '../theme/colors';
import { useLanguage } from '../i18n/LanguageContext';

const Tab = createBottomTabNavigator<DriverTabParamList>();

const ICONS: Record<keyof DriverTabParamList, string> = {
  DriverHome: '🏠',
  Trip: '🚗',
  Earnings: '💰',
  DriverProfile: '👤',
};

export function DriverTabNavigator() {
  const { t } = useLanguage();
  const labels: Record<keyof DriverTabParamList, string> = {
    DriverHome: t('tabs.home'),
    Trip: t('tabs.trip'),
    Earnings: t('tabs.earnings'),
    DriverProfile: t('tabs.profile'),
  };

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.deep,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarIcon: ({ color }) => <Text style={{ fontSize: 20 }}>{ICONS[route.name as keyof DriverTabParamList]}</Text>,
        tabBarLabel: labels[route.name as keyof DriverTabParamList],
        tabBarStyle: { paddingBottom: 6, paddingTop: 6, height: 62 },
      })}
    >
      <Tab.Screen name="DriverHome" component={DriverHomeScreen} />
      <Tab.Screen name="Trip" component={TripScreen} />
      <Tab.Screen name="Earnings" component={EarningsScreen} />
      <Tab.Screen name="DriverProfile" component={DriverProfileScreen} />
    </Tab.Navigator>
  );
}
