import React, { useCallback, useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import MapView, { Marker } from 'react-native-maps';
import { Screen } from '../../components/Screen';
import { Header } from '../../components/Header';
import { Button } from '../../components/Button';
import { StatusBadge } from '../../components/StatusBadge';
import { colors, radius, spacing } from '../../theme/colors';
import { ClientStackParamList } from '../../navigation/types';
import { Order } from '../../types';
import { getOrder, changeOrderStatus, submitOrderReview } from '../../api/orders';
import { extractErrorMessage } from '../../api/client';
import { useOrderSocket } from '../../hooks/useOrderSocket';
import { ReviewModal } from '../../components/ReviewModal';
import { useLanguage } from '../../i18n/LanguageContext';

type Props = NativeStackScreenProps<ClientStackParamList, 'TaxiTracking'>;

export function TaxiTrackingScreen({ route, navigation }: Props) {
  const { t } = useLanguage();
  const { orderId } = route.params;
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reviewVisible, setReviewVisible] = useState(false);
  const [reviewDone, setReviewDone] = useState(false);
  const socket = useOrderSocket(orderId);

  const load = useCallback(async () => {
    try {
      const o = await getOrder(orderId);
      setOrder(o);
      if (o.status === 'completed') setReviewVisible((v) => v || !reviewDone);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderId]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 8000);
    return () => clearInterval(interval);
  }, [load]);

  useEffect(() => {
    if (socket.lastStatus) {
      load();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socket.lastStatus, socket.lastEvent]);

  const handleCancel = async () => {
    if (!order) return;
    try {
      const updated = await changeOrderStatus(order.id, 'cancelled');
      setOrder(updated);
    } catch (e) {
      setError(extractErrorMessage(e));
    }
  };

  if (loading || !order) {
    return (
      <Screen>
        <Header title={t('tracking.orderPrefix')} />
        <View style={styles.center}>
          <Text style={styles.muted}>{t('tracking.loading')}</Text>
        </View>
      </Screen>
    );
  }

  const driverLat = socket.driverLocation?.lat ?? null;
  const driverLng = socket.driverLocation?.lng ?? null;

  return (
    <Screen>
      <Header title={`${t('tracking.orderPrefix')} #${order.id}`} />

      <View style={styles.mapWrap}>
        <MapView
          style={StyleSheet.absoluteFill}
          initialRegion={{
            latitude: order.from_lat,
            longitude: order.from_lng,
            latitudeDelta: 0.05,
            longitudeDelta: 0.05,
          }}
        >
          <Marker coordinate={{ latitude: order.from_lat, longitude: order.from_lng }} pinColor={colors.turquoise} title={t('taxi.from')} />
          <Marker coordinate={{ latitude: order.to_lat, longitude: order.to_lng }} pinColor={colors.deep} title={t('taxi.to')} />
          {driverLat && driverLng ? (
            <Marker coordinate={{ latitude: driverLat, longitude: driverLng }} title={t('home.defaultDriverName')} pinColor="#E0A100" />
          ) : null}
        </MapView>
      </View>

      <ScrollView style={styles.sheet} contentContainerStyle={styles.sheetContent}>
        <View style={styles.statusRow}>
          <StatusBadge status={order.status} />
          {order.estimated_price ? (
            <Text style={styles.price}>{Number(order.final_price ?? order.estimated_price).toLocaleString('ru-RU')} {t('common.somUnit')}</Text>
          ) : null}
        </View>

        <Text style={styles.addressLine} numberOfLines={1}>📍 {order.from_address}</Text>
        <Text style={styles.addressLine} numberOfLines={1}>🏁 {order.to_address}</Text>

        {order.driver ? (
          <View style={styles.driverCard}>
            <View style={styles.driverAvatar}>
              <Text style={styles.driverAvatarText}>{order.driver.name?.[0] ?? 'H'}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.driverName}>{order.driver.name}</Text>
              <Text style={styles.driverMeta}>
                {order.driver.car} · {order.driver.car_number} · ⭐ {order.driver.rating}
              </Text>
            </View>
          </View>
        ) : (
          <Text style={styles.muted}>{t('tracking.searchingDriver')}</Text>
        )}

        {error ? <Text style={styles.errorText}>{error}</Text> : null}

        {(order.status === 'pending' || order.status === 'accepted') && (
          <Button title={t('tracking.cancelOrder')} variant="outline" onPress={handleCancel} style={{ marginTop: spacing.sm }} />
        )}

        {order.status === 'completed' && !reviewDone && (
          <Button title={t('tracking.rateDriver')} onPress={() => setReviewVisible(true)} style={{ marginTop: spacing.sm }} />
        )}

        {order.status === 'completed' && (
          <Button
            title={t('tracking.backHome')}
            variant="secondary"
            onPress={() => navigation.popToTop()}
            style={{ marginTop: spacing.sm }}
          />
        )}
      </ScrollView>

      <ReviewModal
        visible={reviewVisible}
        onClose={() => setReviewVisible(false)}
        onSubmit={async (rating, comment) => {
          await submitOrderReview(order.id, rating, comment);
          setReviewDone(true);
          setReviewVisible(false);
        }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  muted: {
    color: colors.textMuted,
    fontSize: 13,
  },
  mapWrap: {
    height: '38%',
  },
  sheet: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    marginTop: -radius.lg,
  },
  sheetContent: {
    padding: spacing.lg,
    paddingBottom: spacing.xl,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  price: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.text,
  },
  addressLine: {
    fontSize: 14,
    color: colors.text,
    marginTop: 4,
  },
  driverCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.paper,
    borderRadius: radius.md,
    padding: spacing.md,
    marginTop: spacing.md,
  },
  driverAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.deep,
    alignItems: 'center',
    justifyContent: 'center',
  },
  driverAvatarText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 18,
  },
  driverName: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.text,
  },
  driverMeta: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  errorText: {
    color: colors.danger,
    fontSize: 13,
    marginTop: spacing.sm,
    textAlign: 'center',
  },
});
