import React, { useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radius, spacing } from '../theme/colors';
import { TextField } from './TextField';
import { Button } from './Button';
import { searchAddress, reverseGeocode } from '../api/geocode';
import { useLanguage } from '../i18n/LanguageContext';

export interface PickedLocation {
  address: string;
  lat: number;
  lng: number;
}

interface LocationPickerProps {
  label: string;
  value: PickedLocation | null;
  onChange: (location: PickedLocation) => void;
  accentColor?: string;
}

// Web'da react-native-maps ishlamaydi (native-only), shuning uchun manzil
// tanlash asosan matnli qidiruv (Nominatim/Yandex orqali backend) va
// brauzer geolokatsiyasi bilan ishlaydi. Qo'lda koordinata kiritish faqat
// qidiruv umuman natija bermagan holatlar uchun ixtiyoriy zaxira.
export function LocationPicker({ label, value, onChange, accentColor }: LocationPickerProps) {
  const { t } = useLanguage();
  const [visible, setVisible] = useState(false);

  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <Pressable style={styles.field} onPress={() => setVisible(true)}>
        <Text style={[styles.fieldText, !value && styles.placeholder]} numberOfLines={1}>
          {value ? value.address : t('locationPicker.labelWeb')}
        </Text>
      </Pressable>

      <Modal visible={visible} animationType="slide" onRequestClose={() => setVisible(false)} transparent>
        <View style={styles.overlay}>
          <PickerCard
            initial={value}
            accentColor={accentColor ?? colors.deep}
            onCancel={() => setVisible(false)}
            onConfirm={(loc) => {
              onChange(loc);
              setVisible(false);
            }}
          />
        </View>
      </Modal>
    </View>
  );
}

function PickerCard({
  initial,
  accentColor,
  onCancel,
  onConfirm,
}: {
  initial: PickedLocation | null;
  accentColor: string;
  onCancel: () => void;
  onConfirm: (loc: PickedLocation) => void;
}) {
  const { t } = useLanguage();
  const [query, setQuery] = useState(initial?.address ?? '');
  const [resolved, setResolved] = useState<PickedLocation | null>(initial);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [showManual, setShowManual] = useState(false);
  const [manualLat, setManualLat] = useState('');
  const [manualLng, setManualLng] = useState('');

  const handleSearch = async () => {
    if (!query.trim()) return;
    setBusy(true);
    setMessage(null);
    try {
      const result = await searchAddress(query);
      if (!result) {
        setMessage(t('locationPicker.notFoundWeb'));
        setResolved(null);
        return;
      }
      setResolved(result);
      setQuery(result.address);
    } catch {
      setMessage(t('locationPicker.searchUnavailableWeb'));
      setResolved(null);
    } finally {
      setBusy(false);
    }
  };

  const handleUseCurrentLocation = () => {
    if (!('geolocation' in navigator)) {
      setMessage(t('locationPicker.browserNoLocation'));
      return;
    }
    setBusy(true);
    setMessage(null);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        try {
          const result = await reverseGeocode(latitude, longitude);
          const address = result?.address ?? `${t('locationPicker.currentLocation')} (${latitude.toFixed(5)}, ${longitude.toFixed(5)})`;
          setResolved({ address, lat: latitude, lng: longitude });
          setQuery(address);
        } catch {
          const address = `${t('locationPicker.currentLocation')} (${latitude.toFixed(5)}, ${longitude.toFixed(5)})`;
          setResolved({ address, lat: latitude, lng: longitude });
          setQuery(address);
        } finally {
          setBusy(false);
        }
      },
      () => {
        setMessage(t('locationPicker.locationDenied'));
        setBusy(false);
      }
    );
  };

  const applyManualCoords = () => {
    const lat = Number(manualLat);
    const lng = Number(manualLng);
    if (Number.isNaN(lat) || Number.isNaN(lng)) {
      setMessage(t('locationPicker.invalidCoords'));
      return;
    }
    setResolved({ address: query.trim() || `${t('locationPicker.point')}: ${lat.toFixed(5)}, ${lng.toFixed(5)}`, lat, lng });
    setMessage(null);
  };

  const canConfirm = !!resolved;

  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>{t('locationPicker.title')}</Text>

      <View style={styles.searchRow}>
        <View style={{ flex: 1 }}>
          <TextField
            placeholder={t('locationPicker.searchPlaceholderWeb')}
            value={query}
            onChangeText={(text) => {
              setQuery(text);
              setResolved(null);
            }}
            onSubmitEditing={handleSearch}
            style={{ marginBottom: 0 }}
          />
        </View>
        <Pressable style={[styles.searchBtn, { backgroundColor: accentColor }]} onPress={handleSearch}>
          <Text style={styles.searchBtnText}>🔍</Text>
        </Pressable>
      </View>

      <Button title={t('locationPicker.useCurrentLocation')} variant="secondary" onPress={handleUseCurrentLocation} loading={busy} style={{ marginTop: spacing.sm }} />

      {resolved ? (
        <View style={styles.resolvedBox}>
          <Text style={styles.resolvedLabel}>{t('locationPicker.selectedAddress')}</Text>
          <Text style={styles.resolvedAddress}>{resolved.address}</Text>
        </View>
      ) : null}

      {message ? <Text style={styles.message}>{message}</Text> : null}

      <Pressable onPress={() => setShowManual((v) => !v)} style={{ marginTop: spacing.sm }}>
        <Text style={styles.manualToggle}>
          {showManual ? t('locationPicker.manualCoordsToggleHide') : t('locationPicker.manualCoordsToggleShow')}
        </Text>
      </Pressable>

      {showManual ? (
        <View style={styles.coordsRow}>
          <View style={{ flex: 1 }}>
            <TextField label={t('locationPicker.lat')} value={manualLat} onChangeText={setManualLat} keyboardType="numeric" />
          </View>
          <View style={{ flex: 1 }}>
            <TextField label={t('locationPicker.lng')} value={manualLng} onChangeText={setManualLng} keyboardType="numeric" />
          </View>
          <Pressable style={[styles.applyBtn, { backgroundColor: accentColor }]} onPress={applyManualCoords}>
            <Text style={styles.applyBtnText}>OK</Text>
          </Pressable>
        </View>
      ) : null}

      <View style={styles.actionsRow}>
        <View style={styles.actionsFlex}>
          <Button title={t('common.cancel')} variant="outline" onPress={onCancel} />
        </View>
        <View style={styles.actionsFlex}>
          <Button title={t('locationPicker.confirm')} accent={accentColor} disabled={!canConfirm} onPress={() => resolved && onConfirm(resolved)} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: spacing.md,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textMuted,
    marginBottom: 6,
  },
  field: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 14,
  },
  fieldText: {
    fontSize: 15,
    color: colors.text,
  },
  placeholder: {
    color: colors.textMuted,
  },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(15,42,56,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  card: {
    width: '100%',
    maxWidth: 480,
    backgroundColor: '#FFFFFF',
    borderRadius: radius.lg,
    padding: spacing.lg,
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.md,
  },
  searchRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    alignItems: 'center',
  },
  searchBtn: {
    width: 48,
    height: 48,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  searchBtnText: {
    fontSize: 18,
  },
  resolvedBox: {
    backgroundColor: colors.paper,
    borderRadius: radius.md,
    padding: spacing.md,
    marginTop: spacing.md,
  },
  resolvedLabel: {
    fontSize: 11,
    color: colors.textMuted,
    marginBottom: 2,
  },
  resolvedAddress: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
  },
  manualToggle: {
    fontSize: 12,
    color: colors.turquoise,
    fontWeight: '600',
  },
  coordsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    alignItems: 'flex-end',
    marginTop: spacing.sm,
  },
  applyBtn: {
    height: 52,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  applyBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  message: {
    color: colors.warning,
    fontSize: 12,
    marginTop: spacing.sm,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  actionsFlex: {
    flex: 1,
  },
});
