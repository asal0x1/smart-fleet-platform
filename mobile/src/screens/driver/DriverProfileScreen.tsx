import React, { useCallback, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import { colors, radius, spacing } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';
import { TextField } from '../../components/TextField';
import { Button } from '../../components/Button';
import { LanguageModal } from '../../components/LanguageModal';
import { DriverProfile } from '../../types';
import { getDriverProfile, updateDriverProfile, uploadDriverDocument, DocumentField } from '../../api/drivers';
import { extractErrorMessage } from '../../api/client';
import { formatPhoneDisplay } from '../../utils/phone';
import { DriverStackParamList } from '../../navigation/types';
import { showAlert } from '../../utils/alert';
import { useLanguage } from '../../i18n/LanguageContext';

type Nav = NativeStackNavigationProp<DriverStackParamList>;

export function DriverProfileScreen() {
  const { t } = useLanguage();
  const navigation = useNavigation<Nav>();
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState<DriverProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [carModel, setCarModel] = useState('');
  const [carColor, setCarColor] = useState('');
  const [carNumber, setCarNumber] = useState('');
  const [licenseNumber, setLicenseNumber] = useState('');
  const [saving, setSaving] = useState(false);
  const [uploadingField, setUploadingField] = useState<DocumentField | null>(null);
  const [languageModalVisible, setLanguageModalVisible] = useState(false);

  const DOCUMENTS: Array<{ field: DocumentField; label: string }> = [
    { field: 'license_photo', label: t('driverProfile.docLicense') },
    { field: 'tech_passport_photo', label: t('driverProfile.docTechPassport') },
    { field: 'passport_photo', label: t('driverProfile.docPassport') },
    { field: 'car_photo', label: t('driverProfile.docCarPhoto') },
  ];

  const load = useCallback(async () => {
    try {
      const data = await getDriverProfile();
      setProfile(data);
      setCarModel(data.car_model ?? '');
      setCarColor(data.car_color ?? '');
      setCarNumber(data.car_number ?? '');
      setLicenseNumber(data.license_number ?? '');
    } catch (e) {
      showAlert(t('common.error'), extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updateDriverProfile({
        car_model: carModel.trim(),
        car_color: carColor.trim(),
        car_number: carNumber.trim(),
        license_number: licenseNumber.trim(),
      });
      setProfile(updated);
      setEditing(false);
    } catch (e) {
      showAlert(t('common.error'), extractErrorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const handleUploadDocument = async (field: DocumentField) => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      showAlert(t('profile.permissionNeeded'), t('profile.galleryPermission'));
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.7,
    });
    if (result.canceled || !result.assets[0]) return;
    setUploadingField(field);
    try {
      await uploadDriverDocument(field, result.assets[0].uri);
      await load();
    } catch (e) {
      showAlert(t('common.error'), extractErrorMessage(e, t('profile.photoUploadError')));
    } finally {
      setUploadingField(null);
    }
  };

  const confirmLogout = () => {
    showAlert(t('profile.logoutConfirmTitle'), t('profile.logoutConfirmMessage'), [
      { text: t('common.cancel'), style: 'cancel' },
      { text: t('common.logout'), style: 'destructive', onPress: logout },
    ]);
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Text style={styles.header}>{t('profile.title')}</Text>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.infoCard}>
          <Text style={styles.name}>{user?.full_name || t('profile.nameNotSet')}</Text>
          <Text style={styles.phone}>{user ? formatPhoneDisplay(user.phone) : ''}</Text>
          <View style={[styles.statusPill, profile?.is_active ? styles.statusActive : styles.statusPending]}>
            <Text style={styles.statusPillText}>
              {profile?.is_active ? t('driverProfile.approved') : t('driverProfile.pendingApproval')}
            </Text>
          </View>
        </View>

        <Text style={styles.sectionTitle}>{t('driverProfile.carInfo')}</Text>
        {editing ? (
          <View style={styles.card}>
            <TextField label={t('driverProfile.carModel')} value={carModel} onChangeText={setCarModel} />
            <TextField label={t('driverProfile.carColor')} value={carColor} onChangeText={setCarColor} />
            <TextField label={t('driverProfile.carNumber')} value={carNumber} onChangeText={setCarNumber} autoCapitalize="characters" />
            <TextField label={t('driverProfile.licenseNumber')} value={licenseNumber} onChangeText={setLicenseNumber} />
            <Button title={t('common.save')} onPress={handleSave} loading={saving} />
            <Button title={t('common.cancel')} variant="secondary" onPress={() => setEditing(false)} style={{ marginTop: spacing.sm }} />
          </View>
        ) : (
          <View style={styles.card}>
            <InfoRow label={t('driverProfile.carModel')} value={profile?.car_model || '—'} />
            <InfoRow label={t('driverProfile.carColor')} value={profile?.car_color || '—'} />
            <InfoRow label={t('driverProfile.carNumber')} value={profile?.car_number || '—'} />
            <InfoRow label={t('driverProfile.licenseNumber')} value={profile?.license_number || '—'} />
            <Button title={t('common.edit')} variant="outline" onPress={() => setEditing(true)} style={{ marginTop: spacing.sm }} />
          </View>
        )}

        <Text style={styles.sectionTitle}>{t('driverProfile.documentsTitle')}</Text>
        <View style={styles.card}>
          {DOCUMENTS.map((doc) => {
            const uploaded = !!(profile as any)?.[doc.field];
            return (
              <View key={doc.field} style={styles.docRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.docLabel}>{doc.label}</Text>
                  <Text style={[styles.docStatus, uploaded ? styles.docStatusOk : styles.docStatusMissing]}>
                    {uploaded ? t('driverProfile.uploaded') : t('driverProfile.notUploaded')}
                  </Text>
                </View>
                <Button
                  title={uploadingField === doc.field ? t('profile.uploading') : uploaded ? t('driverProfile.replace') : t('driverProfile.upload')}
                  variant="outline"
                  onPress={() => handleUploadDocument(doc.field)}
                  loading={uploadingField === doc.field}
                  style={styles.docBtn}
                />
              </View>
            );
          })}
        </View>

        <Button
          title={t('profile.menuLanguage')}
          variant="outline"
          onPress={() => setLanguageModalVisible(true)}
          style={{ marginTop: spacing.lg }}
        />
        <Button
          title={t('driverProfile.changePassword')}
          variant="outline"
          onPress={() => navigation.navigate('ChangePassword')}
          style={{ marginTop: spacing.sm }}
        />
        <Button title={t('common.logout')} variant="danger" onPress={confirmLogout} style={{ marginTop: spacing.sm }} />
      </ScrollView>

      <LanguageModal visible={languageModalVisible} onClose={() => setLanguageModalVisible(false)} />
    </SafeAreaView>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.paper,
  },
  header: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.text,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: 40,
  },
  infoCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  name: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.text,
  },
  phone: {
    fontSize: 14,
    color: colors.textMuted,
    marginTop: 4,
  },
  statusPill: {
    marginTop: spacing.sm,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: radius.full,
  },
  statusActive: {
    backgroundColor: '#DDF4EA',
  },
  statusPending: {
    backgroundColor: '#FFF3D6',
  },
  statusPillText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.text,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.paper,
  },
  infoLabel: {
    fontSize: 13,
    color: colors.textMuted,
  },
  infoValue: {
    fontSize: 13,
    color: colors.text,
    fontWeight: '600',
  },
  docRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.paper,
    gap: spacing.sm,
  },
  docLabel: {
    fontSize: 13,
    color: colors.text,
    fontWeight: '600',
  },
  docStatus: {
    fontSize: 11,
    marginTop: 2,
  },
  docStatusOk: {
    color: colors.success,
  },
  docStatusMissing: {
    color: colors.warning,
  },
  docBtn: {
    minHeight: 38,
    paddingVertical: 8,
    paddingHorizontal: spacing.sm,
  },
});
