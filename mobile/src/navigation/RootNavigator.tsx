import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { AuthNavigator } from './AuthNavigator';
import { ClientNavigator } from './ClientNavigator';
import { DriverNavigator } from './DriverNavigator';
import { colors } from '../theme/colors';

export function RootNavigator() {
  const { isLoading, isAuthenticated, user } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.splash}>
        <Text style={styles.logo}>Smart Fleet</Text>
        <ActivityIndicator style={{ marginTop: 16 }} color={colors.deep} />
      </View>
    );
  }

  if (!isAuthenticated || !user) {
    return <AuthNavigator />;
  }

  return user.role === 'driver' ? <DriverNavigator /> : <ClientNavigator />;
}

const styles = StyleSheet.create({
  splash: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.paper,
  },
  logo: {
    fontSize: 26,
    fontWeight: '800',
    color: colors.deep,
  },
});
