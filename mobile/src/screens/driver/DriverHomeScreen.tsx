import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Location from 'expo-location';
import { activateKeepAwakeAsync, deactivateKeepAwake } from 'expo-keep-awake';
import { colors, radius, spacing } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';
import { useNotificationSocket, NewOrderEvent } from '../../context/NotificationSocketContext';
import { DriverProfile, Order } from '../../types';
import { getDriverProfile, setDriverOnline, updateDriverLocation } from '../../api/drivers';
import { changeOrderStatus, getAvailableOrders } from '../../api/orders';
import { extractErrorMessage } from '../../api/client';
import { IncomingOrderModal } from '../../components/IncomingOrderModal';
import { NotificationBell } from '../../components/NotificationBell';
import { DriverStackParamList } from '../../navigation/types';
import { showAlert } from '../../utils/alert';
import { useLanguage } from '../../i18n/LanguageContext';

type Nav = NativeStackNavigationProp<DriverStackParamList>;

const LOCATION_INTERVAL_MS = 10000;
const AVAILABLE_ORDERS_INTERVAL_MS = 10000;
const KEEP_AWAKE_TAG = 'driver-online';

export function DriverHomeScreen() {
  const { t } = useLanguage();
  const navigation = useNavigation<Nav>();
  const { user } = useAuth();
  const { subscribe } = useNotificationSocket();
  const [profile, setProfile] = useState<DriverProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [togglingOnline, setTogglingOnline] = useState(false);
  const [incomingOrder, setIncomingOrder] = useState<NewOrderEvent | null>(null);
  const [accepting, setAccepting] = useState(false);
  const [availableOrders, setAvailableOrders] = useState<Order[]>([]);
  const [acceptingId, setAcceptingId] = useState<number | null>(null);
  const locationInterval = useRef<ReturnType<typeof setInterval> | null>(null);
  const availableOrdersInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadProfile = useCallback(async () => {
    try {
      const data = await getDriverProfile();
      setProfile(data);
    } catch (e) {
      showAlert(t('common.error'), extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadProfile();
    }, [loadProfile])
  );

  const loadAvailableOrders = useCallback(async () => {
    try {
      const orders = await getAvailableOrders();
      setAvailableOrders(orders);
    } catch {
      // fon rejimida sokin ishlaydi — xato bo'lsa keyingi urinishda tuzaladi
    }
  }, []);

  useEffect(() => {
    return subscribe((event) => {
      if (event.type === 'new_order' && !incomingOrder) {
        setIncomingOrder(event);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [incomingOrder]);

  const startLocationUpdates = useCallback(async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') return;
    const send = async () => {
      try {
        const pos = await Location.getCurrentPositionAsync({});
        await updateDriverLocation(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy ?? undefined);
      } catch {
        // joylashuv yuborilmasa ham ilova ishlashda davom etadi
      }
    };
    send();
    locationInterval.current = setInterval(send, LOCATION_INTERVAL_MS);
  }, []);

  const stopLocationUpdates = useCallback(() => {
    if (locationInterval.current) {
      clearInterval(locationInterval.current);
      locationInterval.current = null;
    }
  }, []);

  useEffect(() => {
    if (profile?.is_online) {
      startLocationUpdates();
      // Ekran o'chib qolsa JS taymerlari (shu jumladan joylashuv yuborish)
      // to'xtaydi — Expo Go'da haqiqiy fon-rejim joylashuvi ishlamaydi,
      // shuning uchun onlayn bo'lganda ekranni doim yoniq tutamiz.
      activateKeepAwakeAsync(KEEP_AWAKE_TAG);
    } else {
      stopLocationUpdates();
      deactivateKeepAwake(KEEP_AWAKE_TAG);
    }
    return () => {
      stopLocationUpdates();
      deactivateKeepAwake(KEEP_AWAKE_TAG);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile?.is_online]);

  // Yangi buyurtma bildirishnomasi (WS) faqat o'sha payt onlayn bo'lgan
  // haydovchiga, 12 soniya ichida yetadi — agar shu vaqtda ilova ochiq
  // bo'lmasa yoki bildirishnoma o'tkazib yuborilsa, buyurtma umuman
  // ko'rinmay qolardi. Shuning uchun onlayn bo'lganda mavjud (hali hech
  // kimga biriktirilmagan) buyurtmalarni muntazam so'rab turamiz.
  useEffect(() => {
    if (profile?.is_online) {
      loadAvailableOrders();
      availableOrdersInterval.current = setInterval(loadAvailableOrders, AVAILABLE_ORDERS_INTERVAL_MS);
    } else {
      setAvailableOrders([]);
      if (availableOrdersInterval.current) {
        clearInterval(availableOrdersInterval.current);
        availableOrdersInterval.current = null;
      }
    }
    return () => {
      if (availableOrdersInterval.current) {
        clearInterval(availableOrdersInterval.current);
        availableOrdersInterval.current = null;
      }
    };
  }, [profile?.is_online, loadAvailableOrders]);

  const handleToggleOnline = async (value: boolean) => {
    if (!profile) return;
    if (value && !profile.is_active) {
      showAlert(t('driverHome.notApprovedTitle'), t('driverHome.notApprovedMessage'));
      return;
    }
    setTogglingOnline(true);
    try {
      const res = await setDriverOnline(value);
      setProfile((p) => (p ? { ...p, is_online: res.is_online } : p));
    } catch (e) {
      showAlert(t('common.error'), extractErrorMessage(e));
    } finally {
      setTogglingOnline(false);
    }
  };

  const handleAccept = async () => {
    if (!incomingOrder) return;
    setAccepting(true);
    try {
      const order = await changeOrderStatus(incomingOrder.order_id, 'accepted');
      setIncomingOrder(null);
      showAlert(t('driverHome.acceptedTitle'), t('driverHome.acceptedMessage', { id: order.id }), [
        { text: t('common.ok'), onPress: () => navigation.navigate('DriverTabs') },
      ]);
    } catch (e) {
      showAlert(t('driverHome.missedTitle'), extractErrorMessage(e, t('driverHome.missedMessage')));
      setIncomingOrder(null);
    } finally {
      setAccepting(false);
    }
  };

  const handleAcceptAvailable = async (orderId: number) => {
    setAcceptingId(orderId);
    try {
      const order = await changeOrderStatus(orderId, 'accepted');
      setAvailableOrders((prev) => prev.filter((o) => o.id !== orderId));
      showAlert(t('driverHome.acceptedTitle'), t('driverHome.acceptedMessage', { id: order.id }), [
        { text: t('common.ok'), onPress: () => navigation.navigate('DriverTabs') },
      ]);
    } catch (e) {
      showAlert(t('common.error'), extractErrorMessage(e, t('driverHome.missedMessage')));
      loadAvailableOrders();
    } finally {
      setAcceptingId(null);
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.headerRow}>
          <View>
            <Text style={styles.greeting}>{t('home.greetingDriver')}</Text>
            <Text style={styles.name}>{user?.full_name || t('home.defaultDriverName')}</Text>
          </View>
          <View style={styles.headerRight}>
            <NotificationBell onPress={() => navigation.navigate('Notifications')} />
            <View style={styles.onlineRow}>
              <Text style={styles.onlineLabel}>{profile?.is_online ? t('driverHome.online') : t('driverHome.offline')}</Text>
              <Switch
                value={!!profile?.is_online}
                onValueChange={handleToggleOnline}
                disabled={togglingOnline || loading}
                trackColor={{ true: colors.turquoise, false: colors.border }}
              />
            </View>
          </View>
        </View>

        {profile && !profile.is_active ? (
          <View style={styles.warningCard}>
            <Text style={styles.warningText}>{t('driverHome.notApprovedWarning')}</Text>
          </View>
        ) : null}

        <View style={styles.statsGrid}>
          <StatCard label={t('driverHome.rating')} value={profile ? `⭐ ${profile.rating}` : '—'} />
          <StatCard label={t('driverHome.completedTrips')} value={profile ? String(profile.total_trips) : '—'} />
          <StatCard label={t('driverHome.car')} value={profile?.car_model || t('driverHome.carNotSet')} />
          <StatCard label={t('driverHome.documents')} value={profile?.documents_complete ? t('driverHome.documentsComplete') : t('driverHome.documentsMissing')} />
        </View>

        {profile?.is_online ? (
          <View style={styles.availableSection}>
            <Text style={styles.sectionTitle}>{t('driverHome.availableOrders')}</Text>
            {availableOrders.length === 0 ? (
              <Text style={styles.availableEmpty}>{t('driverHome.noAvailableOrders')}</Text>
            ) : (
              availableOrders.map((order) => (
                <View key={order.id} style={styles.orderCard}>
                  <Text style={styles.orderAddress} numberOfLines={1}>📍 {order.from_address}</Text>
                  <Text style={styles.orderAddress} numberOfLines={1}>🏁 {order.to_address}</Text>
                  <View style={styles.orderBottomRow}>
                    <Text style={styles.orderPrice}>
                      {Number(order.estimated_price ?? 0).toLocaleString('ru-RU')} {t('common.somUnit')}
                    </Text>
                    <Pressable
                      style={[styles.acceptBtn, acceptingId === order.id && styles.acceptBtnDisabled]}
                      onPress={() => handleAcceptAvailable(order.id)}
                      disabled={acceptingId !== null}
                    >
                      <Text style={styles.acceptBtnText}>
                        {acceptingId === order.id ? t('driverHome.accepting') : t('driverHome.accept')}
                      </Text>
                    </Pressable>
                  </View>
                </View>
              ))
            )}
          </View>
        ) : null}

        <View style={styles.tipCard}>
          <Text style={styles.tipTitle}>{t('driverHome.tipTitle')}</Text>
          <Text style={styles.tipText}>
            {t('driverHome.tipText')}
            {profile?.is_online ? t('driverHome.tipKeepOpen') : ''}
          </Text>
        </View>
      </ScrollView>

      <IncomingOrderModal
        order={incomingOrder}
        accepting={accepting}
        onAccept={handleAccept}
        onDismiss={() => setIncomingOrder(null)}
      />
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
  content: {
    padding: spacing.lg,
    paddingBottom: 40,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  greeting: {
    fontSize: 14,
    color: colors.textMuted,
  },
  name: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.text,
    marginTop: 2,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  onlineRow: {
    alignItems: 'center',
  },
  onlineLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.textMuted,
    marginBottom: 4,
  },
  warningCard: {
    backgroundColor: '#FFF3D6',
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  warningText: {
    color: '#8A5A00',
    fontSize: 13,
    lineHeight: 18,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  statCard: {
    flexBasis: '47%',
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
  availableSection: {
    marginBottom: spacing.md,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  availableEmpty: {
    fontSize: 13,
    color: colors.textMuted,
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  orderCard: {
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
    marginBottom: 2,
  },
  orderBottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  orderPrice: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.text,
  },
  acceptBtn: {
    backgroundColor: colors.turquoise,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: 9,
  },
  acceptBtnDisabled: {
    opacity: 0.5,
  },
  acceptBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  tipCard: {
    backgroundColor: colors.deep,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  tipTitle: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 14,
    marginBottom: 4,
  },
  tipText: {
    color: '#CFE3E1',
    fontSize: 13,
    lineHeight: 18,
  },
});
