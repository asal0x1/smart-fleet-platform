import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Screen } from '../../components/Screen';
import { Header } from '../../components/Header';
import { Button } from '../../components/Button';
import { LocationPicker, PickedLocation } from '../../components/LocationPicker';
import { colors, radius, spacing } from '../../theme/colors';
import { ClientStackParamList } from '../../navigation/types';
import { Tariff } from '../../types';
import { getTariffs, estimateOrder, createOrder } from '../../api/orders';
import { extractErrorMessage } from '../../api/client';
import { isSameLocation } from '../../utils/geo';
import { useLanguage } from '../../i18n/LanguageContext';

type Props = NativeStackScreenProps<ClientStackParamList, 'TaxiOrder'>;

export function TaxiOrderScreen({ navigation }: Props) {
  const { t } = useLanguage();
  const [from, setFrom] = useState<PickedLocation | null>(null);
  const [to, setTo] = useState<PickedLocation | null>(null);
  const [tariffs, setTariffs] = useState<Tariff[]>([]);
  const [selectedTariff, setSelectedTariff] = useState<Tariff | null>(null);
  const [estimate, setEstimate] = useState<{ estimated_price: number; distance_km: number; duration_min: number } | null>(null);
  const [estimating, setEstimating] = useState(false);
  const [loadingTariffs, setLoadingTariffs] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const list = await getTariffs();
        setTariffs(list);
        if (list.length) setSelectedTariff(list[0]);
      } catch (e) {
        setError(extractErrorMessage(e, t('taxi.tariffsLoadError')));
      } finally {
        setLoadingTariffs(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!from || !to || !selectedTariff) {
      setEstimate(null);
      return;
    }
    if (isSameLocation(from, to)) {
      setEstimate(null);
      setError(t('taxi.sameLocationError'));
      return;
    }
    setError(null);
    let cancelled = false;
    setEstimating(true);
    estimateOrder({
      from_lat: from.lat,
      from_lng: from.lng,
      to_lat: to.lat,
      to_lng: to.lng,
      tariff_id: selectedTariff.id,
    })
      .then((res) => {
        if (!cancelled) setEstimate(res);
      })
      .catch((e) => {
        if (!cancelled) setError(extractErrorMessage(e, t('taxi.estimateError')));
      })
      .finally(() => {
        if (!cancelled) setEstimating(false);
      });
    return () => {
      cancelled = true;
    };
  }, [from, to, selectedTariff]);

  const canSubmit = !!(from && to && selectedTariff && !submitting && !isSameLocation(from, to) && estimate);

  const handleSubmit = async () => {
    if (!from || !to || !selectedTariff) return;
    setError(null);
    setSubmitting(true);
    try {
      const order = await createOrder({
        from_address: from.address,
        from_lat: from.lat,
        from_lng: from.lng,
        to_address: to.address,
        to_lat: to.lat,
        to_lng: to.lng,
        tariff_id: selectedTariff.id,
        payment_method: 'cash',
      });
      navigation.replace('TaxiTracking', { orderId: order.id });
    } catch (e) {
      setError(extractErrorMessage(e, t('taxi.orderError')));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Screen scroll>
      <Header title={t('taxi.title')} />

      <LocationPicker label={t('taxi.from')} value={from} onChange={setFrom} accentColor={colors.module.taxi.accent} />
      <LocationPicker label={t('taxi.to')} value={to} onChange={setTo} accentColor={colors.module.taxi.accent} />

      <Text style={styles.sectionTitle}>{t('taxi.chooseTariff')}</Text>
      {loadingTariffs ? (
        <Text style={styles.muted}>{t('taxi.loadingTariffs')}</Text>
      ) : (
        <View style={styles.tariffList}>
          {tariffs.map((tariff) => (
            <Pressable
              key={tariff.id}
              onPress={() => setSelectedTariff(tariff)}
              style={[styles.tariffCard, selectedTariff?.id === tariff.id && styles.tariffCardSelected]}
            >
              <Text style={[styles.tariffName, selectedTariff?.id === tariff.id && styles.tariffNameSelected]}>
                {tariff.name_uz || tariff.name}
              </Text>
            </Pressable>
          ))}
        </View>
      )}

      <Text style={styles.sectionTitle}>{t('taxi.paymentMethod')}</Text>
      <View style={styles.paymentInfo}>
        <Text style={styles.paymentInfoText}>{t('taxi.cashOnly')}</Text>
        <Text style={styles.paymentInfoNote}>{t('taxi.otherPaymentsSoon')}</Text>
      </View>

      {estimating ? <Text style={styles.muted}>{t('taxi.calculatingPrice')}</Text> : null}
      {estimate ? (
        <View style={styles.estimateBox}>
          <Text style={styles.estimatePrice}>{estimate.estimated_price.toLocaleString('ru-RU')} {t('common.somUnit')}</Text>
          <Text style={styles.estimateMeta}>
            {estimate.distance_km} {t('common.kmUnit')} · {estimate.duration_min} {t('common.minUnit')}
          </Text>
        </View>
      ) : null}

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <Button
        title={submitting ? t('taxi.submitting') : t('taxi.submit')}
        onPress={handleSubmit}
        disabled={!canSubmit}
        loading={submitting}
        accent={colors.module.taxi.deep}
        style={{ marginTop: spacing.md }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
    marginTop: spacing.sm,
    marginBottom: spacing.sm,
  },
  muted: {
    color: colors.textMuted,
    fontSize: 13,
    marginBottom: spacing.sm,
  },
  tariffList: {
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  tariffCard: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  tariffCardSelected: {
    borderColor: colors.module.taxi.deep,
    backgroundColor: '#EAF1F1',
  },
  tariffName: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.text,
  },
  tariffNameSelected: {
    color: colors.module.taxi.deep,
  },
  paymentInfo: {
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  paymentInfoText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
  },
  paymentInfoNote: {
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 4,
  },
  estimateBox: {
    backgroundColor: colors.module.taxi.deep,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  estimatePrice: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: '800',
  },
  estimateMeta: {
    color: '#CFE3E1',
    fontSize: 13,
    marginTop: 2,
  },
  errorText: {
    color: colors.danger,
    fontSize: 13,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
});
