import React, { useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import { colors, radius, spacing } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';
import { TextField } from '../../components/TextField';
import { Button } from '../../components/Button';
import { LanguageModal } from '../../components/LanguageModal';
import { updateProfile, uploadAvatar } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { formatPhoneDisplay } from '../../utils/phone';
import { resolveMediaUrl } from '../../api/config';
import { showAlert } from '../../utils/alert';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ClientStackParamList } from '../../navigation/types';
import { useLanguage } from '../../i18n/LanguageContext';

type Nav = NativeStackNavigationProp<ClientStackParamList>;

export function ProfileScreen() {
  const navigation = useNavigation<Nav>();
  const { t } = useLanguage();
  const { user, setUser, logout } = useAuth();
  const [editing, setEditing] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name ?? '');
  const [email, setEmail] = useState(user?.email ?? '');
  const [saving, setSaving] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [languageModalVisible, setLanguageModalVisible] = useState(false);

  const MENU_ITEMS: Array<{ label: string; action: 'notifications' | 'password' | 'language' | 'soon' }> = [
    { label: t('profile.menuAgreement'), action: 'soon' },
    { label: t('profile.menuNotifications'), action: 'notifications' },
    { label: t('profile.menuLanguage'), action: 'language' },
    { label: t('profile.menuSecurity'), action: 'password' },
  ];

  const handleSave = async () => {
    setError(null);
    setSaving(true);
    try {
      const updated = await updateProfile({ full_name: fullName.trim(), email: email.trim() || undefined });
      setUser(updated);
      setEditing(false);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  const handlePickAvatar = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      showAlert(t('profile.permissionNeeded'), t('profile.galleryPermission'));
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.7,
      allowsEditing: true,
      aspect: [1, 1],
    });
    if (result.canceled || !result.assets[0]) return;
    setUploadingAvatar(true);
    try {
      const updated = await uploadAvatar(result.assets[0].uri);
      setUser(updated);
    } catch (e) {
      showAlert(t('common.error'), extractErrorMessage(e, t('profile.photoUploadError')));
    } finally {
      setUploadingAvatar(false);
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
        <Pressable style={styles.avatarWrap} onPress={handlePickAvatar} disabled={uploadingAvatar}>
          {resolveMediaUrl(user?.avatar || user?.avatar_url) ? (
            <Image source={{ uri: resolveMediaUrl(user?.avatar || user?.avatar_url)! }} style={styles.avatar} />
          ) : (
            <View style={styles.avatarPlaceholder}>
              <Text style={styles.avatarInitial}>{user?.full_name?.[0]?.toUpperCase() ?? '?'}</Text>
            </View>
          )}
          <Text style={styles.avatarEdit}>{uploadingAvatar ? t('profile.uploading') : t('profile.changePhoto')}</Text>
        </Pressable>

        {editing ? (
          <View style={styles.editForm}>
            <TextField label={t('auth.fullName')} value={fullName} onChangeText={setFullName} />
            <TextField label={t('profile.email')} value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
            {error ? <Text style={styles.errorText}>{error}</Text> : null}
            <Button title={t('common.save')} onPress={handleSave} loading={saving} />
            <Button title={t('common.cancel')} variant="secondary" onPress={() => setEditing(false)} style={{ marginTop: spacing.sm }} />
          </View>
        ) : (
          <View style={styles.infoCard}>
            <Text style={styles.name}>{user?.full_name || t('profile.nameNotSet')}</Text>
            <Text style={styles.phone}>{user ? formatPhoneDisplay(user.phone) : ''}</Text>
            <Button title={t('profile.editProfile')} variant="outline" onPress={() => setEditing(true)} style={{ marginTop: spacing.md }} />
          </View>
        )}

        <View style={styles.menu}>
          {MENU_ITEMS.map((item) => (
            <Pressable
              key={item.label}
              style={styles.menuRow}
              onPress={() => {
                if (item.action === 'notifications') navigation.navigate('Notifications');
                else if (item.action === 'password') navigation.navigate('ChangePassword');
                else if (item.action === 'language') setLanguageModalVisible(true);
                else showAlert(item.label, t('common.comingSoon'));
              }}
            >
              <Text style={styles.menuText}>{item.label}</Text>
              <Text style={styles.menuArrow}>›</Text>
            </Pressable>
          ))}
        </View>

        <Button title={t('common.logout')} variant="danger" onPress={confirmLogout} style={{ marginTop: spacing.lg }} />
      </ScrollView>

      <LanguageModal visible={languageModalVisible} onClose={() => setLanguageModalVisible(false)} />
    </SafeAreaView>
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
    paddingBottom: spacing.xl,
  },
  avatarWrap: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  avatar: {
    width: 84,
    height: 84,
    borderRadius: 42,
    backgroundColor: colors.border,
  },
  avatarPlaceholder: {
    width: 84,
    height: 84,
    borderRadius: 42,
    backgroundColor: colors.deep,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitial: {
    color: '#FFFFFF',
    fontSize: 32,
    fontWeight: '800',
  },
  avatarEdit: {
    marginTop: spacing.sm,
    color: colors.turquoise,
    fontSize: 13,
    fontWeight: '600',
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
  editForm: {
    marginBottom: spacing.lg,
  },
  errorText: {
    color: colors.danger,
    fontSize: 13,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  menu: {
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    overflow: 'hidden',
  },
  menuRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: colors.paper,
  },
  menuText: {
    fontSize: 14,
    color: colors.text,
  },
  menuArrow: {
    fontSize: 18,
    color: colors.textMuted,
  },
});
