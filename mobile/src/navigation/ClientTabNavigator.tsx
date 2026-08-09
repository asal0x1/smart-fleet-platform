import React from 'react';
import { Text } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { ClientTabParamList } from './types';
import { ClientHomeScreen } from '../screens/client/ClientHomeScreen';
import { OrdersScreen } from '../screens/client/OrdersScreen';
import { WalletScreen } from '../screens/client/WalletScreen';
import { ProfileScreen } from '../screens/client/ProfileScreen';
import { colors } from '../theme/colors';
import { useLanguage } from '../i18n/LanguageContext';

const Tab = createBottomTabNavigator<ClientTabParamList>();

const ICONS: Record<keyof ClientTabParamList, string> = {
  Home: '🏠',
  Orders: '📋',
  Wallet: '👛',
  Profile: '👤',
};

export function ClientTabNavigator() {
  const { t } = useLanguage();
  const labels: Record<keyof ClientTabParamList, string> = {
    Home: t('tabs.home'),
    Orders: t('tabs.orders'),
    Wallet: t('tabs.wallet'),
    Profile: t('tabs.profile'),
  };

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.deep,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarIcon: ({ color }) => <Text style={{ fontSize: 20 }}>{ICONS[route.name as keyof ClientTabParamList]}</Text>,
        tabBarLabel: labels[route.name as keyof ClientTabParamList],
        tabBarStyle: { paddingBottom: 6, paddingTop: 6, height: 62 },
      })}
    >
      <Tab.Screen name="Home" component={ClientHomeScreen} />
      <Tab.Screen name="Orders" component={OrdersScreen} />
      <Tab.Screen name="Wallet" component={WalletScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}
