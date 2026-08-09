import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { radius } from '../theme/colors';
import { RequestStatus } from '../types';
import { useLanguage } from '../i18n/LanguageContext';

const COLORS: Record<RequestStatus, { bg: string; fg: string }> = {
  pending: { bg: '#FFF3D6', fg: '#8A5A00' },
  contacted: { bg: '#DCEFFB', fg: '#0A5A8C' },
  confirmed: { bg: '#E1E8FF', fg: '#3949AB' },
  completed: { bg: '#DDF4EA', fg: '#1E7A4C' },
  cancelled: { bg: '#FBE0E0', fg: '#B23A3A' },
};

export function RequestStatusBadge({ status }: { status: RequestStatus }) {
  const { t } = useLanguage();
  const c = COLORS[status] ?? COLORS.pending;
  return (
    <View style={[styles.badge, { backgroundColor: c.bg }]}>
      <Text style={[styles.text, { color: c.fg }]}>{t(`requestStatus.${status}`)}</Text>
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
