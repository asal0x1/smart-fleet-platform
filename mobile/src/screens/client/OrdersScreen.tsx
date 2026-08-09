import React, { useCallback, useState } from 'react';
import { FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { CompositeNavigationProp, useNavigation } from '@react-navigation/native';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBadge } from '../../components/StatusBadge';
import { RequestStatusBadge } from '../../components/RequestStatusBadge';
import { colors, radius, spacing } from '../../theme/colors';
import {
  BusRequestItem,
  GiftMemorialRequestItem,
  HeavyEquipmentRequestItem,
  Order,
  PersonalDriverRequestItem,
  WeddingRequestItem,
} from '../../types';
import { getOrders } from '../../api/orders';
import {
  getMyBusRequests,
  getMyGiftMemorialRequests,
  getMyHeavyEquipmentRequests,
  getMyPersonalDriverRequests,
  getMyWeddingRequests,
} from '../../api/requests';
import { extractErrorMessage } from '../../api/client';
import { ClientStackParamList, ClientTabParamList } from '../../navigation/types';
import { useLanguage } from '../../i18n/LanguageContext';
import { TranslationKey } from '../../i18n';

type Nav = CompositeNavigationProp<
  BottomTabNavigationProp<ClientTabParamList, 'Orders'>,
  NativeStackNavigationProp<ClientStackParamList>
>;

// DIQQAT: "kind" nomini diskriminant sifatida ishlatmaymiz — chunki
// GiftMemorialRequestItem'ning o'zida ham "kind" ('gift'|'memorial')
// maydoni bor, spread paytida ular to'qnashib ketardi. Shu sabab alohida
// "moduleType" maydoni ishlatiladi.
type MixedRequest =
  | ({ moduleType: 'wedding' } & WeddingRequestItem)
  | ({ moduleType: 'heavy' } & HeavyEquipmentRequestItem)
  | ({ moduleType: 'personalDriver' } & PersonalDriverRequestItem)
  | ({ moduleType: 'bus' } & BusRequestItem)
  | ({ moduleType: 'giftMemorial' } & GiftMemorialRequestItem);

function heavyCategoryLabel(t: (key: TranslationKey) => string, category: string): string {
  const key = `heavy.cat${category.charAt(0).toUpperCase()}${category.slice(1)}`;
  return t(key as 'heavy.catEarth');
}

function busCategoryLabel(t: (key: TranslationKey) => string, category: string): string {
  const key = `bus.cat${category.charAt(0).toUpperCase()}${category.slice(1)}`;
  return t(key as 'bus.catWedding');
}

function requestTitle(t: (key: TranslationKey) => string, item: MixedRequest): string {
  switch (item.moduleType) {
    case 'wedding':
      return `💍 ${item.car_brand} x${item.car_count}`;
    case 'heavy':
      return `🏗️ ${heavyCategoryLabel(t, item.category)}`;
    case 'personalDriver':
      return `🧑‍✈️ ${item.car_brand}`;
    case 'bus':
      return `🚌 ${item.bus_brand} x${item.bus_count} — ${busCategoryLabel(t, item.category)}`;
    case 'giftMemorial':
      return `${item.kind === 'gift' ? '🎁' : '🕯️'} ${t(item.kind === 'gift' ? 'giftMemorial.tabGift' : 'giftMemorial.tabMemorial')}`;
    default:
      return '';
  }
}

export function OrdersScreen() {
  const { t } = useLanguage();
  const navigation = useNavigation<Nav>();
  const [tab, setTab] = useState<'taxi' | 'requests'>('taxi');
  const [orders, setOrders] = useState<Order[]>([]);
  const [requests, setRequests] = useState<MixedRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOrders = useCallback(async () => {
    try {
      const data = await getOrders();
      setOrders(data);
      setError(null);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadRequests = useCallback(async () => {
    try {
      const [wedding, heavy, personalDriver, bus, giftMemorial] = await Promise.all([
        getMyWeddingRequests(),
        getMyHeavyEquipmentRequests(),
        getMyPersonalDriverRequests(),
        getMyBusRequests(),
        getMyGiftMemorialRequests(),
      ]);
      const merged: MixedRequest[] = [
        ...wedding.map((w) => ({ moduleType: 'wedding' as const, ...w })),
        ...heavy.map((h) => ({ moduleType: 'heavy' as const, ...h })),
        ...personalDriver.map((p) => ({ moduleType: 'personalDriver' as const, ...p })),
        ...bus.map((b) => ({ moduleType: 'bus' as const, ...b })),
        ...giftMemorial.map((g) => ({ moduleType: 'giftMemorial' as const, ...g })),
      ].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setRequests(merged);
      setError(null);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    return tab === 'taxi' ? loadOrders() : loadRequests();
  }, [tab, loadOrders, loadRequests]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Text style={styles.header}>{t('orders.title')}</Text>

      <View style={styles.tabRow}>
        <Pressable style={[styles.tab, tab === 'taxi' && styles.tabActive]} onPress={() => setTab('taxi')}>
          <Text style={[styles.tabText, tab === 'taxi' && styles.tabTextActive]}>{t('orders.tabTaxi')}</Text>
        </Pressable>
        <Pressable style={[styles.tab, tab === 'requests' && styles.tabActive]} onPress={() => setTab('requests')}>
          <Text style={[styles.tabText, tab === 'requests' && styles.tabTextActive]}>{t('orders.tabRequests')}</Text>
        </Pressable>
      </View>

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      {tab === 'taxi' ? (
        <FlatList
          data={orders}
          keyExtractor={(item) => String(item.id)}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
          ListEmptyComponent={!loading ? <Text style={styles.empty}>{t('orders.empty')}</Text> : null}
          renderItem={({ item }) => (
            <Pressable style={styles.card} onPress={() => navigation.navigate('TaxiTracking', { orderId: item.id })}>
              <View style={styles.cardTop}>
                <Text style={styles.cardTitle}>{item.tariff_name ?? t('tracking.orderPrefix')}</Text>
                <StatusBadge status={item.status} />
              </View>
              <Text style={styles.address} numberOfLines={1}>📍 {item.from_address}</Text>
              <Text style={styles.address} numberOfLines={1}>🏁 {item.to_address}</Text>
              <View style={styles.cardBottom}>
                <Text style={styles.date}>{new Date(item.created_at).toLocaleDateString('uz-UZ')}</Text>
                <Text style={styles.price}>
                  {Number(item.final_price ?? item.estimated_price ?? 0).toLocaleString('ru-RU')} {t('common.somUnit')}
                </Text>
              </View>
            </Pressable>
          )}
        />
      ) : (
        <FlatList
          data={requests}
          keyExtractor={(item) => `${item.moduleType}-${item.id}`}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
          ListEmptyComponent={!loading ? <Text style={styles.empty}>{t('orders.emptyRequests')}</Text> : null}
          renderItem={({ item }) => (
            <View style={styles.card}>
              <View style={styles.cardTop}>
                <Text style={styles.cardTitle}>{requestTitle(t, item)}</Text>
                <RequestStatusBadge status={item.status} />
              </View>
              <Text style={styles.address} numberOfLines={1}>📍 {item.address}</Text>
              <View style={styles.cardBottom}>
                <Text style={styles.date}>{new Date(item.created_at).toLocaleDateString('uz-UZ')}</Text>
                {item.estimated_price ? (
                  <Text style={styles.price}>{Number(item.estimated_price).toLocaleString('ru-RU')} {t('common.somUnit')}</Text>
                ) : null}
              </View>
            </View>
          )}
        />
      )}
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
  tabRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    marginBottom: spacing.sm,
  },
  tab: {
    paddingHorizontal: spacing.md,
    paddingVertical: 8,
    borderRadius: radius.full,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: colors.border,
  },
  tabActive: {
    backgroundColor: colors.deep,
    borderColor: colors.deep,
  },
  tabText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text,
  },
  tabTextActive: {
    color: '#FFFFFF',
  },
  list: {
    padding: spacing.lg,
    paddingTop: 0,
    gap: spacing.sm,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.text,
    flexShrink: 1,
    marginRight: spacing.sm,
  },
  address: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 2,
  },
  cardBottom: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
  },
  date: {
    fontSize: 12,
    color: colors.textMuted,
  },
  price: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
  },
  errorText: {
    color: colors.danger,
    fontSize: 13,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  empty: {
    textAlign: 'center',
    color: colors.textMuted,
    marginTop: spacing.xl,
  },
});
