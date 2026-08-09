import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Screen } from '../../components/Screen';
import { Header } from '../../components/Header';
import { Button } from '../../components/Button';
import { TextField } from '../../components/TextField';
import { ChipGroup } from '../../components/ChipGroup';
import { DateField } from '../../components/DateField';
import { LocationPicker, PickedLocation } from '../../components/LocationPicker';
import { colors, radius, spacing } from '../../theme/colors';
import { ClientStackParamList } from '../../navigation/types';
import { submitGiftMemorialRequest } from '../../api/requests';
import { extractErrorMessage } from '../../api/client';
import { isValidUzPhone, normalizePhone } from '../../utils/phone';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../i18n/LanguageContext';
import { GiftMemorialKind } from '../../types';
import { formatDateForApi } from '../../utils/date';

type Props = NativeStackScreenProps<ClientStackParamList, 'GiftMemorial'>;

export function GiftMemorialScreen({ navigation }: Props) {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [kind, setKind] = useState<GiftMemorialKind>('gift');
  const DECORATIONS: Array<{ key: 'flowers' | 'balloons' | 'ribbons'; label: string }> = [
    { key: 'flowers', label: t('wedding.decorFlowers') },
    { key: 'balloons', label: t('wedding.decorBalloons') },
    { key: 'ribbons', label: t('wedding.decorRibbons') },
  ];
  const [decoration, setDecoration] = useState<'flowers' | 'balloons' | 'ribbons'>('flowers');
  const [location, setLocation] = useState<PickedLocation | null>(null);
  const [date, setDate] = useState<Date | null>(null);
  const [time, setTime] = useState<Date | null>(null);
  const [contactName, setContactName] = useState(user?.full_name ?? '');
  const [contactPhone, setContactPhone] = useState(user?.phone ?? '+998');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ estimated_price: number; message: string } | null>(null);

  const handleSubmit = async () => {
    setError(null);
    if (!location) {
      setError(t('giftMemorial.addressRequired'));
      return;
    }
    if (!date) {
      setError(t('giftMemorial.dateRequired'));
      return;
    }
    if (!contactName.trim()) {
      setError(t('giftMemorial.nameRequired'));
      return;
    }
    if (!isValidUzPhone(contactPhone)) {
      setError(t('giftMemorial.phoneInvalid'));
      return;
    }
    setSubmitting(true);
    try {
      const res = await submitGiftMemorialRequest({
        kind,
        decoration_type: kind === 'gift' ? decoration : undefined,
        address: location.address,
        date: formatDateForApi(date),
        time: time ? time.toTimeString().slice(0, 5) : undefined,
        contact_name: contactName.trim(),
        contact_phone: normalizePhone(contactPhone),
        notes: notes.trim() || undefined,
      });
      setResult({ estimated_price: res.estimated_price, message: res.message });
    } catch (e) {
      setError(extractErrorMessage(e, t('giftMemorial.submitError')));
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <Screen>
        <Header title={t('giftMemorial.title')} />
        <View style={styles.successBox}>
          <Text style={styles.successIcon}>✅</Text>
          <Text style={styles.successTitle}>{t('giftMemorial.successTitle')}</Text>
          <Text style={styles.successText}>{result.message}</Text>
          <Text style={styles.successPrice}>{result.estimated_price.toLocaleString('ru-RU')} {t('common.somUnit')} {t('wedding.estimatedPrice')}</Text>
          <Button title={t('tracking.backHome')} onPress={() => navigation.popToTop()} style={{ marginTop: spacing.lg }} />
        </View>
      </Screen>
    );
  }

  return (
    <Screen scroll>
      <Header title={t('giftMemorial.title')} />

      <View style={styles.tabRow}>
        <Pressable
          onPress={() => setKind('gift')}
          style={[styles.tab, kind === 'gift' && styles.tabActive]}
        >
          <Text style={[styles.tabText, kind === 'gift' && styles.tabTextActive]}>🎁 {t('giftMemorial.tabGift')}</Text>
        </Pressable>
        <Pressable
          onPress={() => setKind('memorial')}
          style={[styles.tab, kind === 'memorial' && styles.tabActive]}
        >
          <Text style={[styles.tabText, kind === 'memorial' && styles.tabTextActive]}>🕯️ {t('giftMemorial.tabMemorial')}</Text>
        </Pressable>
      </View>

      {kind === 'gift' ? (
        <>
          <Text style={styles.sectionTitle}>{t('giftMemorial.decorationType')}</Text>
          <ChipGroup
            options={DECORATIONS.map((d) => d.label)}
            value={DECORATIONS.find((d) => d.key === decoration)?.label ?? ''}
            onChange={(label) => setDecoration(DECORATIONS.find((d) => d.label === label)?.key ?? 'flowers')}
            accentColor={colors.module.gift.deep}
          />
        </>
      ) : null}

      <LocationPicker
        label={t('giftMemorial.address')}
        value={location}
        onChange={setLocation}
        accentColor={kind === 'gift' ? colors.module.gift.accent : colors.module.memorial.accent}
      />
      <DateField label={t('giftMemorial.date')} mode="date" value={date} onChange={setDate} minimumDate={new Date()} />
      <DateField label={t('giftMemorial.time')} mode="time" value={time} onChange={setTime} />

      <TextField label={t('giftMemorial.contactName')} value={contactName} onChangeText={setContactName} />
      <TextField label={t('giftMemorial.contactPhone')} value={contactPhone} onChangeText={setContactPhone} keyboardType="phone-pad" />
      <TextField label={t('giftMemorial.notes')} value={notes} onChangeText={setNotes} multiline style={{ minHeight: 70 }} />

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <Button
        title={t('giftMemorial.submit')}
        onPress={handleSubmit}
        loading={submitting}
        accent={kind === 'gift' ? colors.module.gift.deep : colors.module.memorial.deep}
        style={{ marginTop: spacing.sm }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  tabRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
  },
  tabActive: {
    backgroundColor: colors.module.gift.deep,
    borderColor: colors.module.gift.deep,
  },
  tabText: {
    fontSize: 13,
    fontWeight: '700',
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
    color: colors.module.gift.deep,
  },
});
