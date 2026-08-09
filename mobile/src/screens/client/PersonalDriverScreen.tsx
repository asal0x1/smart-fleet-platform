import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Screen } from '../../components/Screen';
import { Header } from '../../components/Header';
import { Button } from '../../components/Button';
import { TextField } from '../../components/TextField';
import { ChipGroup } from '../../components/ChipGroup';
import { DateField } from '../../components/DateField';
import { LocationPicker, PickedLocation } from '../../components/LocationPicker';
import { colors, spacing } from '../../theme/colors';
import { ClientStackParamList } from '../../navigation/types';
import { submitPersonalDriverRequest } from '../../api/requests';
import { extractErrorMessage } from '../../api/client';
import { isValidUzPhone, normalizePhone } from '../../utils/phone';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../i18n/LanguageContext';
import { ContractDuration, DriverExperience } from '../../types';
import { formatDateForApi } from '../../utils/date';

type Props = NativeStackScreenProps<ClientStackParamList, 'PersonalDriver'>;

const CAR_BRANDS = ['Chevrolet', 'Lexus', 'Toyota', 'Mercedes-Benz'];
const EXPERIENCE_KEYS: DriverExperience[] = ['1-3', '3-5', '5-10', '10+'];
const DURATION_KEYS: ContractDuration[] = ['1_day', '1_week', '1_month', '3_months', '6_months', '1_year'];

export function PersonalDriverScreen({ navigation }: Props) {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [carBrand, setCarBrand] = useState(CAR_BRANDS[0]);
  const [experience, setExperience] = useState<DriverExperience>('1-3');
  const [duration, setDuration] = useState<ContractDuration>('1_month');
  const [location, setLocation] = useState<PickedLocation | null>(null);
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [contactName, setContactName] = useState(user?.full_name ?? '');
  const [contactPhone, setContactPhone] = useState(user?.phone ?? '+998');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ estimated_price: number; message: string } | null>(null);

  const experienceLabels = EXPERIENCE_KEYS.map((key) => t(`personalDriver.experienceOptions.${key}` as 'personalDriver.experienceOptions.1-3'));
  const durationLabels = DURATION_KEYS.map((key) => t(`personalDriver.durationOptions.${key}` as 'personalDriver.durationOptions.1_day'));

  const handleSubmit = async () => {
    setError(null);
    if (!location) {
      setError(t('personalDriver.addressRequired'));
      return;
    }
    if (!startDate) {
      setError(t('personalDriver.dateRequired'));
      return;
    }
    if (!contactName.trim()) {
      setError(t('personalDriver.nameRequired'));
      return;
    }
    if (!isValidUzPhone(contactPhone)) {
      setError(t('personalDriver.phoneInvalid'));
      return;
    }
    setSubmitting(true);
    try {
      const res = await submitPersonalDriverRequest({
        car_brand: carBrand,
        driver_experience: experience,
        contract_duration: duration,
        address: location.address,
        start_date: formatDateForApi(startDate),
        contact_name: contactName.trim(),
        contact_phone: normalizePhone(contactPhone),
        notes: notes.trim() || undefined,
      });
      setResult({ estimated_price: res.estimated_price, message: res.message });
    } catch (e) {
      setError(extractErrorMessage(e, t('personalDriver.submitError')));
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <Screen>
        <Header title={t('personalDriver.title')} />
        <View style={styles.successBox}>
          <Text style={styles.successIcon}>✅</Text>
          <Text style={styles.successTitle}>{t('personalDriver.successTitle')}</Text>
          <Text style={styles.successText}>{result.message}</Text>
          <Text style={styles.successPrice}>{result.estimated_price.toLocaleString('ru-RU')} {t('common.somUnit')} {t('wedding.estimatedPrice')}</Text>
          <Button title={t('tracking.backHome')} onPress={() => navigation.popToTop()} style={{ marginTop: spacing.lg }} />
        </View>
      </Screen>
    );
  }

  return (
    <Screen scroll>
      <Header title={t('personalDriver.title')} />

      <Text style={styles.sectionTitle}>{t('personalDriver.carBrand')}</Text>
      <ChipGroup options={CAR_BRANDS} value={carBrand} onChange={setCarBrand} accentColor={colors.module.driver.deep} />

      <Text style={styles.sectionTitle}>{t('personalDriver.experience')}</Text>
      <ChipGroup
        options={experienceLabels}
        value={experienceLabels[EXPERIENCE_KEYS.indexOf(experience)]}
        onChange={(label) => setExperience(EXPERIENCE_KEYS[experienceLabels.indexOf(label)])}
        accentColor={colors.module.driver.deep}
      />

      <Text style={styles.sectionTitle}>{t('personalDriver.duration')}</Text>
      <ChipGroup
        options={durationLabels}
        value={durationLabels[DURATION_KEYS.indexOf(duration)]}
        onChange={(label) => setDuration(DURATION_KEYS[durationLabels.indexOf(label)])}
        accentColor={colors.module.driver.deep}
      />

      <LocationPicker label={t('personalDriver.address')} value={location} onChange={setLocation} accentColor={colors.module.driver.accent} />
      <DateField label={t('personalDriver.startDate')} mode="date" value={startDate} onChange={setStartDate} minimumDate={new Date()} />

      <TextField label={t('personalDriver.contactName')} value={contactName} onChangeText={setContactName} />
      <TextField label={t('personalDriver.contactPhone')} value={contactPhone} onChangeText={setContactPhone} keyboardType="phone-pad" />
      <TextField label={t('personalDriver.notes')} value={notes} onChangeText={setNotes} multiline style={{ minHeight: 70 }} />

      <Text style={styles.agreementNote}>{t('personalDriver.agreementNote')}</Text>

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <Button
        title={t('personalDriver.submit')}
        onPress={handleSubmit}
        loading={submitting}
        accent={colors.module.driver.deep}
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
  agreementNote: {
    fontSize: 12,
    color: colors.textMuted,
    marginBottom: spacing.sm,
    lineHeight: 17,
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
    color: colors.module.driver.deep,
  },
});
