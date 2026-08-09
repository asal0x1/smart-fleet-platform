import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, radius } from '../theme/colors';
import { OrderStatus } from '../types';
import { useLanguage } from '../i18n/LanguageContext';

const COLORS: Record<OrderStatus, { bg: string; fg: string }> = {
  pending: { bg: '#FFF3D6', fg: '#8A5A00' },
  accepted: { bg: '#DCEFFB', fg: '#0A5A8C' },
  driver_arrived: { bg: '#E1E8FF', fg: '#3949AB' },
  ongoing: { bg: '#DDF4EA', fg: '#1E7A4C' },
  completed: { bg: '#DDF4EA', fg: '#1E7A4C' },
  cancelled: { bg: '#FBE0E0', fg: '#B23A3A' },
};

export function StatusBadge({ status }: { status: OrderStatus }) {
  const { t } = useLanguage();
  const c = COLORS[status] ?? COLORS.pending;
  return (
    <View style={[styles.badge, { backgroundColor: c.bg }]}>
      <Text style={[styles.text, { color: c.fg }]}>{t(`status.${status}`)}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: radius.full,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: 12,
    fontWeight: '700',
  },
});
