import React, { useMemo, useState } from 'react';
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
import { HeavyCategory } from '../../types';
import { submitHeavyEquipmentRequest } from '../../api/requests';
import { extractErrorMessage } from '../../api/client';
import { isValidUzPhone, normalizePhone } from '../../utils/phone';
import { useAuth } from '../../context/AuthContext';
import { showAlert } from '../../utils/alert';
import { useLanguage } from '../../i18n/LanguageContext';
import uzLocale from '../../i18n/locales/uz';
import { formatDateForApi } from '../../utils/date';

type Props = NativeStackScreenProps<ClientStackParamList, 'HeavyEquipment'>;

// Texnika turi kaliti (equipment lug'atidagi kalit nomi). Foydalanuvchiga
// tanlangan tilda ko'rsatiladi, lekin backendga (va operator email'iga)
// har doim o'zbekcha kanonik nom yuboriladi — admin paneli va operator
// faqat o'zbek tilida ishlaydi, shu bilan ma'lumotlar bazasi bir xilligi
// saqlanadi.
const EQUIPMENT_KEYS: Record<HeavyCategory, Array<keyof typeof uzLocale.heavy.equipment>> = {
  earth: ['excavator', 'bulldozer', 'grader'],
  lift: ['crane', 'dumpTruck'],
  road: ['roller', 'concreteMixer', 'concretePump'],
  loader: ['frontLoader'],
};

const CATEGORY_KEYS: HeavyCategory[] = ['earth', 'lift', 'road', 'loader'];

export function HeavyEquipmentScreen({ navigation }: Props) {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [category, setCategory] = useState<HeavyCategory>('earth');
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const [customName, setCustomName] = useState('');
  const [customItems, setCustomItems] = useState<Record<string, number>>({});
  const [location, setLocation] = useState<PickedLocation | null>(null);
  const [startDate, setStartDate] = useState<Date | null>(null);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [durationDays, setDurationDays] = useState(1);
  const [contactName, setContactName] = useState(user?.full_name ?? '');
  const [contactPhone, setContactPhone] = useState(user?.phone ?? '+998');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ estimated_price: number; message: string } | null>(null);

  const activeItemKeys = EQUIPMENT_KEYS[category];

  const totalSelected = useMemo(() => {
    const catCount = activeItemKeys.reduce((sum, key) => sum + (quantities[key] ?? 0), 0);
    const customCount = Object.values(customItems).reduce((sum, q) => sum + q, 0);
    return catCount + customCount;
  }, [quantities, customItems, activeItemKeys]);

  const addCustomItem = () => {
    const name = customName.trim();
    if (!name) return;
    setCustomItems((prev) => ({ ...prev, [name]: (prev[name] ?? 0) + 1 }));
    setCustomName('');
  };

  const handleCategoryChange = (next: HeavyCategory) => {
    if (next === category) return;
    if (totalSelected > 0) {
      showAlert(
        t('heavy.switchWarnTitle'),
        t('heavy.switchWarnMessage'),
        [
          { text: t('common.cancel'), style: 'cancel' },
          {
            text: t('heavy.switchWarnConfirm'),
            style: 'destructive',
            onPress: () => {
              setQuantities({});
              setCustomItems({});
              setCategory(next);
            },
          },
        ]
      );
      return;
    }
    setCategory(next);
  };

  const handleSubmit = async () => {
    setError(null);
    const items = [
      ...activeItemKeys
        .filter((key) => (quantities[key] ?? 0) > 0)
        .map((key) => ({ name: uzLocale.heavy.equipment[key], quantity: quantities[key] })),
      ...Object.entries(customItems)
        .filter(([, q]) => q > 0)
        .map(([name, quantity]) => ({ name, quantity })),
    ];
    if (items.length === 0) {
      setError(t('heavy.noItemsSelected'));
      return;
    }
    if (!location) {
      setError(t('heavy.addressRequired'));
      return;
    }
    if (!startDate) {
      setError(t('heavy.dateRequired'));
      return;
    }
    if (!contactName.trim() || !isValidUzPhone(contactPhone)) {
      setError(t('heavy.contactInvalid'));
      return;
    }

    setSubmitting(true);
    try {
      const res = await submitHeavyEquipmentRequest({
        category,
        items,
        address: location.address,
        lat: location.lat,
        lng: location.lng,
        start_date: formatDateForApi(startDate),
        start_time: startTime ? startTime.toTimeString().slice(0, 5) : undefined,
        duration_days: durationDays,
        contact_name: contactName.trim(),
        contact_phone: normalizePhone(contactPhone),
        notes: notes.trim() || undefined,
      });
      setResult({ estimated_price: res.estimated_price, message: res.message });
    } catch (e) {
      setError(extractErrorMessage(e, t('heavy.submitError')));
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <Screen>
        <Header title={t('heavy.title')} />
        <View style={styles.successBox}>
          <Text style={styles.successIcon}>✅</Text>
          <Text style={styles.successTitle}>{t('heavy.successTitle')}</Text>
          <Text style={styles.successText}>{result.message}</Text>
          <Text style={styles.successPrice}>{result.estimated_price.toLocaleString('ru-RU')} {t('common.somUnit')} {t('wedding.estimatedPrice')}</Text>
          <Button title={t('tracking.backHome')} onPress={() => navigation.popToTop()} style={{ marginTop: spacing.lg }} />
        </View>
      </Screen>
    );
  }

  return (
    <Screen scroll>
      <Header title={t('heavy.title')} />

      <View style={styles.tabRow}>
        {CATEGORY_KEYS.map((key) => (
          <Pressable
            key={key}
            onPress={() => handleCategoryChange(key)}
            style={[styles.tab, category === key && styles.tabActive]}
          >
            <Text style={[styles.tabText, category === key && styles.tabTextActive]}>
              {t(`heavy.cat${key.charAt(0).toUpperCase()}${key.slice(1)}` as 'heavy.catEarth')}
            </Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.card}>
        {activeItemKeys.map((key) => (
          <Stepper
            key={key}
            label={t(`heavy.equipment.${key}`)}
            value={quantities[key] ?? 0}
            min={0}
            max={20}
            onChange={(v) => setQuantities((prev) => ({ ...prev, [key]: v }))}
          />
        ))}

        {Object.keys(customItems).length > 0 && (
          <View style={styles.customList}>
            {Object.entries(customItems).map(([name, qty]) => (
              <Stepper
                key={name}
                label={name}
                value={qty}
                min={0}
                max={20}
                onChange={(v) => setCustomItems((prev) => ({ ...prev, [name]: v }))}
              />
            ))}
          </View>
        )}

        <View style={styles.customAddRow}>
          <View style={{ flex: 1 }}>
            <TextField placeholder={t('heavy.addCustomPlaceholder')} value={customName} onChangeText={setCustomName} style={{ marginBottom: 0 }} />
          </View>
          <Pressable style={styles.addBtn} onPress={addCustomItem}>
            <Text style={styles.addBtnText}>+</Text>
          </Pressable>
        </View>
      </View>

      <LocationPicker label={t('heavy.projectAddress')} value={location} onChange={setLocation} accentColor={colors.module.heavy.accent} />
      <DateField label={t('heavy.startDate')} mode="date" value={startDate} onChange={setStartDate} minimumDate={new Date()} />
      <DateField label={t('heavy.startTime')} mode="time" value={startTime} onChange={setStartTime} />
      <Stepper label={t('heavy.durationDays')} value={durationDays} onChange={setDurationDays} min={1} max={90} />

      <TextField label={t('heavy.contactName')} value={contactName} onChangeText={setContactName} />
      <TextField label={t('heavy.contactPhone')} value={contactPhone} onChangeText={setContactPhone} keyboardType="phone-pad" />
      <TextField label={t('heavy.notes')} value={notes} onChangeText={setNotes} multiline style={{ minHeight: 70 }} />

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <Button
        title={`${t('heavy.submit')}${totalSelected ? ` (${totalSelected})` : ''}`}
        onPress={handleSubmit}
        loading={submitting}
        accent={colors.module.heavy.deep}
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
    backgroundColor: colors.module.heavy.deep,
    borderColor: colors.module.heavy.deep,
  },
  tabText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.text,
  },
  tabTextActive: {
    color: '#FFFFFF',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  customList: {
    marginTop: spacing.xs,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: spacing.sm,
  },
  customAddRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  addBtn: {
    width: 44,
    height: 44,
    borderRadius: radius.sm,
    backgroundColor: colors.module.heavy.deep,
    alignItems: 'center',
    justifyContent: 'center',
  },
  addBtnText: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '700',
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
    color: colors.module.heavy.deep,
  },
});
