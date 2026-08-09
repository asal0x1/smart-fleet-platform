import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Screen } from '../../components/Screen';
import { Header } from '../../components/Header';
import { Button } from '../../components/Button';
import { TextField } from '../../components/TextField';
import { Stepper } from '../../components/Stepper';
import { DateField } from '../../components/DateField';
import { LocationPicker, PickedLocation } from '../../components/LocationPicker';
import { colors, radius, spacing } from '../../theme/colors';
import { ClientStackParamList } from '../../navigation/types';
import { submitBusRequest } from '../../api/requests';
import { extractErrorMessage } from '../../api/client';
import { isValidUzPhone, normalizePhone } from '../../utils/phone';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../i18n/LanguageContext';
import { BusCategory } from '../../types';
import { formatDateForApi } from '../../utils/date';

type Props = NativeStackScreenProps<ClientStackParamList, 'BusBooking'>;

const CATEGORY_KEYS: BusCategory[] = ['wedding', 'memorial', 'tour'];
const BUS_BRAND_SUGGESTIONS = ['Isuzu', 'MAN', 'Mercedes-Benz'];

export function BusBookingScreen({ navigation }: Props) {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [category, setCategory] = useState<BusCategory>('wedding');
  const [busBrand, setBusBrand] = useState(BUS_BRAND_SUGGESTIONS[0]);
  const [busCount, setBusCount] = useState(1);
  const [location, setLocation] = useState<PickedLocation | null>(null);
  const [date, setDate] = useState<Date | null>(null);
  const [time, setTime] = useState<Date | null>(null);
  const [durationHours, setDurationHours] = useState(3);
  const [contactName, setContactName] = useState(user?.full_name ?? '');
  const [contactPhone, setContactPhone] = useState(user?.phone ?? '+998');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ estimated_price: number; message: string } | null>(null);

  const categoryLabel = (key: BusCategory) => t(`bus.cat${key.charAt(0).toUpperCase()}${key.slice(1)}` as 'bus.catWedding');

  const handleSubmit = async () => {
    setError(null);
    if (!busBrand.trim()) {
      setError(t('bus.busBrandRequired'));
      return;
    }
    if (!location) {
      setError(t('bus.addressRequired'));
      return;
    }
    if (!date) {
      setError(t('bus.dateRequired'));
      return;
    }
    if (!contactName.trim()) {
      setError(t('bus.nameRequired'));
      return;
    }
    if (!isValidUzPhone(contactPhone)) {
      setError(t('bus.phoneInvalid'));
      return;
    }
    setSubmitting(true);
    try {
      const res = await submitBusRequest({
        category,
        bus_brand: busBrand.trim(),
        bus_count: busCount,
        address: location.address,
        date: formatDateForApi(date),
        time: time ? time.toTimeString().slice(0, 5) : undefined,
        duration_hours: durationHours,
        contact_name: contactName.trim(),
        contact_phone: normalizePhone(contactPhone),
        notes: notes.trim() || undefined,
      });
      setResult({ estimated_price: res.estimated_price, message: res.message });
    } catch (e) {
      setError(extractErrorMessage(e, t('bus.submitError')));
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <Screen>
        <Header title={t('bus.title')} />
        <View style={styles.successBox}>
          <Text style={styles.successIcon}>✅</Text>
          <Text style={styles.successTitle}>{t('bus.successTitle')}</Text>
          <Text style={styles.successText}>{result.message}</Text>
          <Text style={styles.successPrice}>{result.estimated_price.toLocaleString('ru-RU')} {t('common.somUnit')} {t('wedding.estimatedPrice')}</Text>
          <Button title={t('tracking.backHome')} onPress={() => navigation.popToTop()} style={{ marginTop: spacing.lg }} />
        </View>
      </Screen>
    );
  }

  return (
    <Screen scroll>
      <Header title={t('bus.title')} />

      <View style={styles.tabRow}>
        {CATEGORY_KEYS.map((key) => (
          <Pressable
            key={key}
            onPress={() => setCategory(key)}
            style={[styles.tab, category === key && styles.tabActive]}
          >
            <Text style={[styles.tabText, category === key && styles.tabTextActive]}>{categoryLabel(key)}</Text>
          </Pressable>
        ))}
      </View>

      <Text style={styles.sectionTitle}>{t('bus.busBrand')}</Text>
      <View style={styles.brandRow}>
        {BUS_BRAND_SUGGESTIONS.map((brand) => (
          <Pressable
            key={brand}
            onPress={() => setBusBrand(brand)}
            style={[styles.brandChip, busBrand === brand && styles.brandChipActive]}
          >
            <Text style={[styles.brandChipText, busBrand === brand && styles.brandChipTextActive]}>{brand}</Text>
          </Pressable>
        ))}
      </View>
      <TextField value={busBrand} onChangeText={setBusBrand} />

      <Stepper label={t('bus.busCount')} value={busCount} onChange={setBusCount} min={1} max={20} />

      <LocationPicker label={t('bus.address')} value={location} onChange={setLocation} accentColor={colors.module.bus.accent} />
      <DateField label={t('bus.date')} mode="date" value={date} onChange={setDate} minimumDate={new Date()} />
      <DateField label={t('bus.time')} mode="time" value={time} onChange={setTime} />
      <Stepper label={t('bus.duration')} value={durationHours} onChange={setDurationHours} min={1} max={24} />

      <TextField label={t('bus.contactName')} value={contactName} onChangeText={setContactName} />
      <TextField label={t('bus.contactPhone')} value={contactPhone} onChangeText={setContactPhone} keyboardType="phone-pad" />
      <TextField label={t('bus.notes')} value={notes} onChangeText={setNotes} multiline style={{ minHeight: 70 }} />

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <Button
        title={t('bus.submit')}
        onPress={handleSubmit}
        loading={submitting}
        accent={colors.module.bus.deep}
        style={{ marginTop: spacing.sm }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  tabRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
    marginBottom: spacing.md,
  },
  tab: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: radius.full,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: colors.border,
  },
  tabActive: {
    backgroundColor: colors.module.bus.deep,
    borderColor: colors.module.bus.deep,
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.text,
  },
  tabTextActive: {
    color: '#FFFFFF',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  brandRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  brandChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: 9,
    borderRadius: radius.full,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: '#FFFFFF',
  },
  brandChipActive: {
    backgroundColor: colors.module.bus.deep,
    borderColor: colors.module.bus.deep,
  },
  brandChipText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text,
  },
  brandChipTextActive: {
    color: '#FFFFFF',
  },
  errorText: {
    color: colors.danger,
    fontSize: 13,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  successBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.xl,
  },
  successIcon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  successTitle: {
    fontSize: 19,
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  successText: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  successPrice: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.module.bus.deep,
  },
});
