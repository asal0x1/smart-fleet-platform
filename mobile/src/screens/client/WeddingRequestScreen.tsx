import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Screen } from '../../components/Screen';
import { Header } from '../../components/Header';
import { Button } from '../../components/Button';
import { TextField } from '../../components/TextField';
import { ChipGroup } from '../../components/ChipGroup';
import { Stepper } from '../../components/Stepper';
import { DateField } from '../../components/DateField';
import { LocationPicker, PickedLocation } from '../../components/LocationPicker';
import { colors, spacing } from '../../theme/colors';
import { ClientStackParamList } from '../../navigation/types';
import { submitWeddingRequest } from '../../api/requests';
import { extractErrorMessage } from '../../api/client';
import { isValidUzPhone, normalizePhone } from '../../utils/phone';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../i18n/LanguageContext';
import { formatDateForApi } from '../../utils/date';

type Props = NativeStackScreenProps<ClientStackParamList, 'WeddingRequest'>;

const CAR_BRANDS = ['Mercedes-Benz', 'Rolls Royce', 'BMW', 'Porsche'];

export function WeddingRequestScreen({ navigation }: Props) {
  const { t } = useLanguage();
  const { user } = useAuth();
  const DECORATIONS: Array<{ key: 'flowers' | 'balloons' | 'ribbons'; label: string }> = [
    { key: 'flowers', label: t('wedding.decorFlowers') },
    { key: 'balloons', label: t('wedding.decorBalloons') },
    { key: 'ribbons', label: t('wedding.decorRibbons') },
  ];
  const [carBrand, setCarBrand] = useState(CAR_BRANDS[0]);
  const [carCount, setCarCount] = useState(1);
  const [decoration, setDecoration] = useState<'flowers' | 'balloons' | 'ribbons'>('flowers');
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

  const handleSubmit = async () => {
    setError(null);
    if (!location) {
      setError(t('wedding.addressRequired'));
      return;
    }
    if (!date) {
      setError(t('wedding.dateRequired'));
      return;
    }
    if (!contactName.trim()) {
      setError(t('wedding.nameRequired'));
      return;
    }
    if (!isValidUzPhone(contactPhone)) {
      setError(t('wedding.phoneInvalid'));
      return;
    }
    setSubmitting(true);
    try {
      const res = await submitWeddingRequest({
        car_brand: carBrand,
        car_count: carCount,
        decoration_type: decoration,
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
      setError(extractErrorMessage(e, t('wedding.submitError')));
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <Screen>
        <Header title={t('wedding.title')} />
        <View style={styles.successBox}>
          <Text style={styles.successIcon}>✅</Text>
          <Text style={styles.successTitle}>{t('wedding.successTitle')}</Text>
          <Text style={styles.successText}>{result.message}</Text>
          <Text style={styles.successPrice}>{result.estimated_price.toLocaleString('ru-RU')} {t('common.somUnit')} {t('wedding.estimatedPrice')}</Text>
          <Button title={t('tracking.backHome')} onPress={() => navigation.popToTop()} style={{ marginTop: spacing.lg }} />
        </View>
      </Screen>
    );
  }

  return (
    <Screen scroll>
      <Header title={t('wedding.title')} />

      <Text style={styles.sectionTitle}>{t('wedding.carBrand')}</Text>
      <ChipGroup options={CAR_BRANDS} value={carBrand} onChange={setCarBrand} accentColor={colors.module.wedding.deep} />

      <Stepper label={t('wedding.carCount')} value={carCount} onChange={setCarCount} min={1} max={20} />

      <Text style={styles.sectionTitle}>{t('wedding.decorationType')}</Text>
      <ChipGroup
        options={DECORATIONS.map((d) => d.label)}
        value={DECORATIONS.find((d) => d.key === decoration)?.label ?? ''}
        onChange={(label) => setDecoration(DECORATIONS.find((d) => d.label === label)?.key ?? 'flowers')}
        accentColor={colors.module.wedding.deep}
      />

      <LocationPicker label={t('wedding.address')} value={location} onChange={setLocation} accentColor={colors.module.wedding.accent} />

      <DateField label={t('wedding.date')} mode="date" value={date} onChange={setDate} minimumDate={new Date()} />
      <DateField label={t('wedding.time')} mode="time" value={time} onChange={setTime} />
      <Stepper label={t('wedding.duration')} value={durationHours} onChange={setDurationHours} min={1} max={24} />

      <TextField label={t('wedding.contactName')} value={contactName} onChangeText={setContactName} />
      <TextField label={t('wedding.contactPhone')} value={contactPhone} onChangeText={setContactPhone} keyboardType="phone-pad" />
      <TextField label={t('wedding.notes')} value={notes} onChangeText={setNotes} multiline style={{ minHeight: 70 }} />

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <Button
        title={t('wedding.submit')}
        onPress={handleSubmit}
        loading={submitting}
        accent={colors.module.wedding.deep}
        style={{ marginTop: spacing.sm }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
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
    color: colors.module.wedding.deep,
  },
});
