import React, { useCallback, useEffect, useState } from 'react';
import { FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { Header } from '../../components/Header';
import { Screen } from '../../components/Screen';
import { colors, radius, spacing } from '../../theme/colors';
import { AppNotification } from '../../types';
import { getNotifications, markAllNotificationsRead, markNotificationRead } from '../../api/notifications';
import { extractErrorMessage } from '../../api/client';
import { useNotificationSocket } from '../../context/NotificationSocketContext';
import { useLanguage } from '../../i18n/LanguageContext';
import { TranslationKey } from '../../i18n';

function timeAgo(iso: string, t: (key: TranslationKey, params?: Record<string, string | number>) => string) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return t('notifications.justNow');
  if (minutes < 60) return t('notifications.minutesAgo', { n: minutes });
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return t('notifications.hoursAgo', { n: hours });
  const days = Math.floor(hours / 24);
  return t('notifications.daysAgo', { n: days });
}

export function NotificationsScreen() {
  const { t } = useLanguage();
  const navigation = useNavigation();
  const { subscribe } = useNotificationSocket();
  const [items, setItems] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const { results } = await getNotifications();
      setItems(results);
      setError(null);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  // Ekran ochiq turganda yangi bildirishnoma kelsa ro'yxatni yangilaymiz
  useEffect(() => subscribe((event) => {
    if (event.type === 'notification') load();
  }), [subscribe, load]);

  const handleMarkRead = async (item: AppNotification) => {
    if (item.is_read) return;
    setItems((prev) => prev.map((n) => (n.id === item.id ? { ...n, is_read: true } : n)));
    try {
      await markNotificationRead(item.id);
    } catch {
      // lokal holat qoladi, keyingi load() haqiqiy holatni tiklaydi
    }
  };

  const handleMarkAll = async () => {
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    try {
      await markAllNotificationsRead();
    } catch {
      load();
    }
  };

  const hasUnread = items.some((n) => !n.is_read);

  return (
    <Screen>
      <Header
        title={t('notifications.title')}
        right={
          hasUnread ? (
            <Pressable onPress={handleMarkAll}>
              <Text style={styles.markAll}>{t('notifications.markAll')}</Text>
            </Pressable>
          ) : undefined
        }
      />
      {error ? <Text style={styles.errorText}>{error}</Text> : null}
      <FlatList
        data={items}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
        ListEmptyComponent={!loading ? <Text style={styles.empty}>{t('notifications.empty')}</Text> : null}
        renderItem={({ item }) => (
          <Pressable style={[styles.card, !item.is_read && styles.cardUnread]} onPress={() => handleMarkRead(item)}>
            {!item.is_read ? <View style={styles.dot} /> : null}
            <View style={{ flex: 1 }}>
              <Text style={styles.title}>{item.title}</Text>
              {item.body ? <Text style={styles.body}>{item.body}</Text> : null}
              <Text style={styles.time}>{timeAgo(item.created_at, t)}</Text>
            </View>
          </Pressable>
        )}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  markAll: {
    color: colors.turquoise,
    fontSize: 13,
    fontWeight: '600',
  },
  list: {
    padding: spacing.lg,
    paddingTop: spacing.sm,
  },
  card: {
    flexDirection: 'row',
    gap: spacing.sm,
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardUnread: {
    borderColor: colors.turquoise,
    backgroundColor: '#F2FBFA',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.turquoise,
    marginTop: 6,
  },
  title: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
  },
  body: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 2,
  },
  time: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 6,
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
