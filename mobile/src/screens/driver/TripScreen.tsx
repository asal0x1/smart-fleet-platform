import React, { useCallback, useEffect, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, radius, spacing } from '../../theme/colors';
import { Order, OrderStatus } from '../../types';
import { getOrders, changeOrderStatus } from '../../api/orders';
import { extractErrorMessage } from '../../api/client';
import { Button } from '../../components/Button';
import { StatusBadge } from '../../components/StatusBadge';
import { useOrderSocket } from '../../hooks/useOrderSocket';
import { showAlert } from '../../utils/alert';
import { useLanguage } from '../../i18n/LanguageContext';
import { TranslationKey } from '../../i18n';

const POLL_INTERVAL_MS = 12000;

const ACTIVE_STATUSES: OrderStatus[] = ['accepted', 'driver_arrived', 'ongoing'];

type TFn = (key: TranslationKey) => string;

function buildSteps(t: TFn): Array<{ status: OrderStatus; label: string }> {
  return [
    { status: 'accepted', label: t('trip.step1') },
    { status: 'driver_arrived', label: t('trip.step2') },
    { status: 'ongoing', label: t('trip.step3') },
    { status: 'completed', label: t('trip.step4') },
  ];
}

function buildNextAction(t: TFn): Partial<Record<OrderStatus, { next: OrderStatus; label: string }>> {
  return {
    accepted: { next: 'driver_arrived', label: t('trip.action1') },
    driver_arrived: { next: 'ongoing', label: t('trip.action2') },
    ongoing: { next: 'completed', label: t('trip.action3') },
  };
}

export function TripScreen() {
  const { t } = useLanguage();
  const STEPS = buildSteps(t);
  const NEXT_ACTION = buildNextAction(t);
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);

  const load = useCallback(async () => {
    try {
      const orders = await getOrders();
      const active = orders.find((o) => ACTIVE_STATUSES.includes(o.status));
      setOrder(active ?? null);
    } catch (e) {
      showAlert(t('common.error'), extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
      // Zaxira: agar WebSocket xabarni o'tkazib yuborsa (masalan mijoz
      // buyurtmani bekor qilganda), baribir bir necha soniyada aniqlanadi.
      const interval = setInterval(load, POLL_INTERVAL_MS);
      return () => clearInterval(interval);
    }, [load])
  );

  const socket = useOrderSocket(order?.id ?? null);
  useEffect(() => {
    if (socket.lastStatus) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socket.lastStatus, socket.lastEvent]);

  const handleAdvance = async () => {
    if (!order) return;
    const action = NEXT_ACTION[order.status];
    if (!action) return;
    setActing(true);
    try {
      const updated = await changeOrderStatus(order.id, action.next);
      if (updated.status === 'completed') {
        showAlert(t('trip.completedTitle'), t('trip.completedMessage'));
        setOrder(null);
      } else {
        setOrder(updated);
      }
    } catch (e) {
      showAlert(t('common.error'), extractErrorMessage(e));
    } finally {
      setActing(false);
    }
  };

  const handleCancel = () => {
    if (!order) return;
    showAlert(t('trip.cancelConfirmTitle'), t('trip.cancelConfirmMessage'), [
      { text: t('trip.cancelConfirmNo'), style: 'cancel' },
      {
        text: t('trip.cancelConfirmYes'),
        style: 'destructive',
        onPress: async () => {
          setActing(true);
          try {
            await changeOrderStatus(order.id, 'cancelled');
            setOrder(null);
          } catch (e) {
            showAlert(t('common.error'), extractErrorMessage(e));
          } finally {
            setActing(false);
          }
        },
      },
    ]);
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Text style={styles.header}>{t('trip.title')}</Text>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      >
        {!order ? (
          <View style={styles.emptyBox}>
            <Text style={styles.emptyIcon}>🚗</Text>
            <Text style={styles.emptyText}>{t('trip.empty')}</Text>
            <Text style={styles.emptySub}>{t('trip.emptySub')}</Text>
          </View>
        ) : (
          <View style={styles.card}>
            <View style={styles.cardTop}>
              <Text style={styles.orderId}>{t('trip.orderPrefix')} #{order.id}</Text>
              <StatusBadge status={order.status} />
            </View>

            <View style={styles.steps}>
              {STEPS.map((step, idx) => {
                const currentIdx = STEPS.findIndex((s) => s.status === order.status);
                const done = idx <= currentIdx;
                return (
                  <View key={step.status} style={styles.stepRow}>
                    <View style={[styles.stepDot, done && styles.stepDotDone]} />
                    <Text style={[styles.stepLabel, done && styles.stepLabelDone]}>{step.label}</Text>
                  </View>
                );
              })}
            </View>

            <Text style={styles.address} numberOfLines={2}>📍 {order.from_address}</Text>
            <Text style={styles.address} numberOfLines={2}>🏁 {order.to_address}</Text>

            <View style={styles.priceRow}>
              <Text style={styles.price}>
                {Number(order.final_price ?? order.estimated_price ?? 0).toLocaleString('ru-RU')} {t('common.somUnit')}
              </Text>
              <Text style={styles.paymentMethod}>
                {order.payment_method === 'cash' ? t('trip.paymentCash') : order.payment_method === 'click' ? t('trip.paymentClick') : t('trip.paymentPayme')}
              </Text>
            </View>

            {NEXT_ACTION[order.status] ? (
              <Button
                title={NEXT_ACTION[order.status]!.label}
                onPress={handleAdvance}
                loading={acting}
                style={{ marginTop: spacing.md }}
              />
            ) : null}

            <Button title={t('trip.cancelTrip')} variant="outline" onPress={handleCancel} disabled={acting} style={{ marginTop: spacing.sm }} />
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
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
    flexGrow: 1,
  },
  emptyBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 80,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  emptyText: {
    fontSize: 17,
    fontWeight: '700',
    color: colors.text,
  },
  emptySub: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 4,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: radius.lg,
    padding: spacing.lg,
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  orderId: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.text,
  },
  steps: {
    marginBottom: spacing.md,
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: 6,
  },
  stepDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.border,
  },
  stepDotDone: {
    backgroundColor: colors.turquoise,
  },
  stepLabel: {
    fontSize: 13,
    color: colors.textMuted,
  },
  stepLabelDone: {
    color: colors.text,
    fontWeight: '600',
  },
  address: {
    fontSize: 14,
    color: colors.text,
    marginBottom: 4,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  price: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.text,
  },
  paymentMethod: {
    fontSize: 13,
    color: colors.textMuted,
  },
});
