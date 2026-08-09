import React, { useEffect, useState } from 'react';
import { Modal, StyleSheet, Text, View } from 'react-native';
import { colors, radius, spacing } from '../theme/colors';
import { Button } from './Button';
import { NewOrderEvent } from '../context/NotificationSocketContext';
import { useLanguage } from '../i18n/LanguageContext';

interface IncomingOrderModalProps {
  order: NewOrderEvent | null;
  onAccept: () => void;
  onDismiss: () => void;
  accepting?: boolean;
}

const TIMEOUT_SECONDS = 12;

export function IncomingOrderModal({ order, onAccept, onDismiss, accepting }: IncomingOrderModalProps) {
  const { t } = useLanguage();
  const [secondsLeft, setSecondsLeft] = useState(TIMEOUT_SECONDS);

  useEffect(() => {
    if (!order) return;
    setSecondsLeft(TIMEOUT_SECONDS);
    const interval = setInterval(() => {
      setSecondsLeft((s) => {
        if (s <= 1) {
          clearInterval(interval);
          onDismiss();
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [order]);

  if (!order) return null;

  return (
    <Modal visible transparent animationType="slide">
      <View style={styles.overlay}>
        <View style={styles.card}>
          <View style={styles.timerRow}>
            <Text style={styles.timerLabel}>{t('incomingOrder.title')}</Text>
            <View style={styles.timerBadge}>
              <Text style={styles.timerText}>{secondsLeft}s</Text>
            </View>
          </View>

          <Text style={styles.address} numberOfLines={2}>📍 {order.from_address}</Text>
          <Text style={styles.address} numberOfLines={2}>🏁 {order.to_address}</Text>

          <View style={styles.metaRow}>
            <Text style={styles.meta}>{order.distance_km ? `${order.distance_km} ${t('common.kmUnit')}` : ''}</Text>
            <Text style={styles.price}>{Number(order.estimated_price).toLocaleString('ru-RU')} {t('common.somUnit')}</Text>
          </View>

          <View style={styles.actions}>
            <View style={styles.actionFlex}>
              <Button title={t('incomingOrder.decline')} variant="outline" onPress={onDismiss} />
            </View>
            <View style={styles.actionFlex}>
              <Button title={t('incomingOrder.accept')} onPress={onAccept} loading={accepting} />
            </View>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(15,42,56,0.55)',
    justifyContent: 'flex-end',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    padding: spacing.lg,
  },
  timerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  timerLabel: {
    fontSize: 17,
    fontWeight: '800',
    color: colors.text,
  },
  timerBadge: {
    backgroundColor: colors.warning,
    borderRadius: radius.full,
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  timerText: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  address: {
    fontSize: 14,
    color: colors.text,
    marginBottom: 4,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
  meta: {
    fontSize: 13,
    color: colors.textMuted,
  },
  price: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.deep,
  },
  actions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  actionFlex: {
    flex: 1,
  },
});
