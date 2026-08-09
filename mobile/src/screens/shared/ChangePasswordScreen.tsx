import React, { useState } from 'react';
import { StyleSheet, Text } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Screen } from '../../components/Screen';
import { Header } from '../../components/Header';
import { TextField } from '../../components/TextField';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme/colors';
import { changePassword } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { tokenStorage } from '../../utils/storage';
import { showAlert } from '../../utils/alert';
import { useLanguage } from '../../i18n/LanguageContext';

export function ChangePasswordScreen() {
  const { t } = useLanguage();
  const navigation = useNavigation();
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);
    if (!oldPassword) {
      setError(t('changePassword.currentRequired'));
      return;
    }
    if (newPassword.length < 6) {
      setError(t('auth.passwordTooShort'));
      return;
    }
    if (newPassword !== confirmPassword) {
      setError(t('changePassword.mismatch'));
      return;
    }
    if (newPassword === oldPassword) {
      setError(t('changePassword.sameAsOld'));
      return;
    }
    setLoading(true);
    try {
      const tokens = await changePassword(oldPassword, newPassword);
      await tokenStorage.setTokens(tokens.access_token, tokens.refresh_token);
      showAlert(t('changePassword.success'), t('changePassword.successMessage'), [
        { text: t('common.ok'), onPress: () => navigation.goBack() },
      ]);
    } catch (e) {
      setError(extractErrorMessage(e, t('changePassword.error')));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen scroll>
      <Header title={t('changePassword.title')} />

      <TextField label={t('changePassword.currentPassword')} value={oldPassword} onChangeText={setOldPassword} secureTextEntry />
      <TextField label={t('changePassword.newPassword')} value={newPassword} onChangeText={setNewPassword} secureTextEntry placeholder={t('auth.passwordMinHint')} />
      <TextField label={t('changePassword.confirmPassword')} value={confirmPassword} onChangeText={setConfirmPassword} secureTextEntry />

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <Button title={t('common.save')} onPress={handleSubmit} loading={loading} style={{ marginTop: spacing.sm }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  errorText: {
    color: colors.danger,
    fontSize: 13,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
});
