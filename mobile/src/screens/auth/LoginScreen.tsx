import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Screen } from '../../components/Screen';
import { TextField } from '../../components/TextField';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';
import { extractErrorMessage } from '../../api/client';
import { AuthStackParamList } from '../../navigation/types';
import { isValidUzPhone, normalizePhone } from '../../utils/phone';
import { useLanguage } from '../../i18n/LanguageContext';

type Props = NativeStackScreenProps<AuthStackParamList, 'Login'>;

export function LoginScreen({ navigation }: Props) {
  const { t } = useLanguage();
  const { login } = useAuth();
  const [phone, setPhone] = useState('+998');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setError(null);
    if (!isValidUzPhone(phone)) {
      setError(t('auth.phoneInvalid'));
      return;
    }
    if (password.length < 6) {
      setError(t('auth.passwordTooShort'));
      return;
    }
    setLoading(true);
    try {
      await login(normalizePhone(phone), password);
    } catch (e) {
      setError(extractErrorMessage(e, t('auth.loginError')));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen scroll>
      <View style={styles.header}>
        <Text style={styles.logo}>{t('auth.appName')}</Text>
        <Text style={styles.subtitle}>{t('auth.loginSubtitle')}</Text>
      </View>

      <TextField
        label={t('auth.phone')}
        value={phone}
        onChangeText={setPhone}
        keyboardType="phone-pad"
        placeholder={t('auth.phonePlaceholder')}
        autoCapitalize="none"
      />
      <TextField
        label={t('auth.password')}
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        placeholder={t('auth.passwordPlaceholder')}
      />

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <Button title={t('auth.login')} onPress={onSubmit} loading={loading} style={{ marginTop: spacing.sm }} />

      <Button
        title={t('auth.forgotPassword')}
        variant="secondary"
        onPress={() => navigation.navigate('ForgotPassword')}
        style={{ marginTop: spacing.sm }}
      />

      <View style={styles.footer}>
        <Text style={styles.footerText}>{t('auth.noAccount')}</Text>
        <Button title={t('auth.register')} variant="outline" onPress={() => navigation.navigate('Register')} style={{ marginTop: spacing.sm }} />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    marginTop: spacing.xl,
    marginBottom: spacing.xl,
    alignItems: 'center',
  },
  logo: {
    fontSize: 28,
    fontWeight: '800',
    color: colors.deep,
  },
  subtitle: {
    fontSize: 14,
    color: colors.textMuted,
    marginTop: spacing.xs,
  },
  errorText: {
    color: colors.danger,
    fontSize: 13,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  footer: {
    marginTop: spacing.xl,
    alignItems: 'stretch',
  },
  footerText: {
    textAlign: 'center',
    color: colors.textMuted,
    fontSize: 13,
  },
});
