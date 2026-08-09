import React, { useCallback, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, radius, spacing } from '../../theme/colors';
import { DriverProfile, Order } from '../../types';
import { getDriverProfile } from '../../api/drivers';
import { getOrders } from '../../api/orders';
import { useLanguage } from '../../i18n/LanguageContext';

export function EarningsScreen() {
  const { t } = useLanguage();
  const [profile, setProfile] = useState<DriverProfile | null>(null);
  const [completedOrders, setCompletedOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [driverProfile, orders] = await Promise.all([getDriverProfile(), getOrders('completed')]);
      setProfile(driverProfile);
      setCompletedOrders(orders);
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const totalEarned = completedOrders.reduce((sum, o) => sum + Number(o.final_price ?? o.estimated_price ?? 0), 0);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Text style={styles.header}>{t('earnings.title')}</Text>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      >
        <View style={styles.summaryCard}>
          <Text style={styles.summaryLabel}>{t('earnings.summaryLabel')}</Text>
          <Text style={styles.summaryValue}>{totalEarned.toLocaleString('ru-RU')} {t('common.somUnit')}</Text>
        </View>

        <View style={styles.statsGrid}>
          <StatCard label={t('earnings.totalTrips')} value={profile ? String(profile.total_trips) : '—'} />
          <StatCard label={t('earnings.rating')} value={profile ? `⭐ ${profile.rating}` : '—'} />
        </View>

        <View style={styles.noteCard}>
          <Text style={styles.noteText}>{t('earnings.noteText')}</Text>
        </View>

        <Text style={styles.sectionTitle}>{t('earnings.completedTripsTitle')}</Text>
        {completedOrders.length === 0 ? (
          <Text style={styles.empty}>{t('earnings.empty')}</Text>
        ) : (
          completedOrders.map((o) => (
            <View key={o.id} style={styles.orderRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.orderAddress} numberOfLines={1}>{o.to_address}</Text>
                <Text style={styles.orderDate}>{new Date(o.created_at).toLocaleDateString('uz-UZ')}</Text>
              </View>
              <Text style={styles.orderPrice}>{Number(o.final_price ?? o.estimated_price ?? 0).toLocaleString('ru-RU')}</Text>
            </View>
          ))
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.paper,
  },
  header: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.text,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: 40,
  },
  summaryCard: {
    backgroundColor: colors.deep,
    borderRadius: radius.lg,
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  summaryLabel: {
    color: '#CFE3E1',
    fontSize: 13,
  },
  summaryValue: {
    color: '#FFFFFF',
    fontSize: 28,
    fontWeight: '800',
    marginTop: 4,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.text,
  },
  statLabel: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 4,
  },
  noteCard: {
    backgroundColor: '#FFF3D6',
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.lg,
  },
  noteText: {
    color: '#8A5A00',
    fontSize: 12,
    lineHeight: 17,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  empty: {
    color: colors.textMuted,
    fontSize: 13,
  },
  orderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  orderAddress: {
    fontSize: 13,
    color: colors.text,
    fontWeight: '600',
  },
  orderDate: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  orderPrice: {
    fontSize: 14,
    fontWeight: '800',
    color: colors.text,
  },
});
