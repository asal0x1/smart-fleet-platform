import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Modal, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import MapView, { Region } from 'react-native-maps';
import * as Location from 'expo-location';
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

const TASHKENT_REGION: Region = {
  latitude: 41.311081,
  longitude: 69.240562,
  latitudeDelta: 0.08,
  longitudeDelta: 0.08,
};

export function LocationPicker({ label, value, onChange, accentColor }: LocationPickerProps) {
  const { t } = useLanguage();
  const [visible, setVisible] = useState(false);

  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <Pressable style={styles.field} onPress={() => setVisible(true)}>
        <Text style={[styles.fieldText, !value && styles.placeholder]} numberOfLines={1}>
          {value ? value.address : t('locationPicker.label')}
        </Text>
      </Pressable>

      <Modal visible={visible} animationType="slide" onRequestClose={() => setVisible(false)}>
        <MapPickerModal
          initial={value}
          accentColor={accentColor ?? colors.deep}
          onCancel={() => setVisible(false)}
          onConfirm={(loc) => {
            onChange(loc);
            setVisible(false);
          }}
        />
      </Modal>
    </View>
  );
}

function MapPickerModal({
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
  const [region, setRegion] = useState<Region>(
    initial
      ? { latitude: initial.lat, longitude: initial.lng, latitudeDelta: 0.02, longitudeDelta: 0.02 }
      : TASHKENT_REGION
  );
  const [address, setAddress] = useState(initial?.address ?? '');
  const [query, setQuery] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [locating, setLocating] = useState(false);
  const [resolvingAddress, setResolvingAddress] = useState(false);

  const useCurrentLocation = useCallback(async () => {
    setLocating(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setSearchError(t('locationPicker.locationDenied'));
        return;
      }
      const pos = await Location.getCurrentPositionAsync({});
      setRegion({
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude,
        latitudeDelta: 0.02,
        longitudeDelta: 0.02,
      });
    } catch {
      setSearchError(t('locationPicker.locationUnavailable'));
    } finally {
      setLocating(false);
    }
  }, []);

  useEffect(() => {
    if (!initial) {
      useCurrentLocation();
    }
    // faqat bir marta, modal ochilganda
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setSearching(true);
    setSearchError(null);
    try {
      const result = await searchAddress(query);
      if (!result) {
        setSearchError(t('locationPicker.notFound'));
        return;
      }
      setRegion({ latitude: result.lat, longitude: result.lng, latitudeDelta: 0.02, longitudeDelta: 0.02 });
      setAddress(result.address);
    } catch {
      setSearchError(t('locationPicker.searchUnavailable'));
    } finally {
      setSearching(false);
    }
  }, [query]);

  const handleRegionChangeComplete = useCallback(async (r: Region) => {
    setRegion(r);
    setResolvingAddress(true);
    try {
      const result = await reverseGeocode(r.latitude, r.longitude);
      setAddress(result?.address ?? `${t('locationPicker.point')}: ${r.latitude.toFixed(5)}, ${r.longitude.toFixed(5)}`);
    } catch {
      setAddress(`${t('locationPicker.point')}: ${r.latitude.toFixed(5)}, ${r.longitude.toFixed(5)}`);
    } finally {
      setResolvingAddress(false);
    }
  }, []);

  return (
    <View style={styles.modalRoot}>
      <View style={styles.searchBar}>
        <TextField
          placeholder={t('locationPicker.searchPlaceholder')}
          value={query}
          onChangeText={setQuery}
          onSubmitEditing={handleSearch}
          returnKeyType="search"
          style={styles.searchInput}
        />
      </View>

      <View style={styles.mapWrap}>
        <MapView
          style={StyleSheet.absoluteFill}
          initialRegion={region}
          region={region}
          onRegionChangeComplete={handleRegionChangeComplete}
        />
        <View pointerEvents="none" style={styles.centerPinWrap}>
          <View style={[styles.centerPin, { backgroundColor: accentColor }]} />
        </View>
        <Pressable style={styles.locateBtn} onPress={useCurrentLocation}>
          {locating ? <ActivityIndicator color={colors.deep} /> : <Text style={styles.locateBtnText}>📍</Text>}
        </Pressable>
      </View>

      <View style={styles.bottomSheet}>
        {searching || resolvingAddress ? (
          <ActivityIndicator style={{ marginBottom: spacing.sm }} />
        ) : (
          <Text style={styles.addressPreview} numberOfLines={2}>
            {address || t('locationPicker.pickOnMapHint')}
          </Text>
        )}
        {searchError ? <Text style={styles.searchErrorText}>{searchError}</Text> : null}

        <View style={styles.actionsRow}>
          <View style={styles.actionsFlex}>
            <Button title={t('common.cancel')} variant="outline" onPress={onCancel} />
          </View>
          <View style={styles.actionsFlex}>
            <Button
              title={t('locationPicker.confirm')}
              accent={accentColor}
              onPress={() =>
                onConfirm({
                  address: address || `${t('locationPicker.point')}: ${region.latitude.toFixed(5)}, ${region.longitude.toFixed(5)}`,
                  lat: region.latitude,
                  lng: region.longitude,
                })
              }
            />
          </View>
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
  modalRoot: {
    flex: 1,
    backgroundColor: colors.paper,
    paddingTop: Platform.OS === 'ios' ? 56 : 24,
  },
  searchBar: {
    paddingHorizontal: spacing.md,
  },
  searchInput: {
    marginBottom: 0,
  },
  mapWrap: {
    flex: 1,
    marginTop: spacing.sm,
  },
  centerPinWrap: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerPin: {
    width: 18,
    height: 18,
    borderRadius: 9,
    marginBottom: 40,
    borderWidth: 3,
    borderColor: '#FFFFFF',
  },
  locateBtn: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
  },
  locateBtnText: {
    fontSize: 20,
  },
  bottomSheet: {
    backgroundColor: '#FFFFFF',
    padding: spacing.md,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
  },
  addressPreview: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  searchErrorText: {
    color: colors.warning,
    fontSize: 12,
    marginBottom: spacing.sm,
  },
  actionsRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  actionsFlex: {
    flex: 1,
  },
});
