import React, { useState } from 'react';
import { StyleSheet, Text } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Screen } from '../../components/Screen';
import { TextField } from '../../components/TextField';
import { Button } from '../../components/Button';
import { Header } from '../../components/Header';
import { colors, spacing } from '../../theme/colors';
import { AuthStackParamList } from '../../navigation/types';
import { isValidUzPhone, normalizePhone } from '../../utils/phone';
import { sendOtp, resetPassword } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { tokenStorage } from '../../utils/storage';
import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../i18n/LanguageContext';

type Props = NativeStackScreenProps<AuthStackParamList, 'ForgotPassword'>;

export function ForgotPasswordScreen({ navigation }: Props) {
  const { t } = useLanguage();
  const { refreshUser } = useAuth();
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [phone, setPhone] = useState('+998');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const handleSendOtp = async () => {
    setError(null);
    if (!isValidUzPhone(phone)) {
      setError(t('auth.phoneInvalid'));
      return;
    }
    setLoading(true);
    try {
      await sendOtp(normalizePhone(phone));
      setInfo(t('auth.otpSentInfo'));
      setStep('otp');
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setError(null);
    if (otp.length < 4) {
      setError(t('auth.otpIncomplete'));
      return;
    }
    if (newPassword.length < 6) {
      setError(t('auth.passwordTooShort'));
      return;
    }
    setLoading(true);
    try {
      const tokens = await resetPassword(normalizePhone(phone), otp, newPassword);
      await tokenStorage.setTokens(tokens.access_token, tokens.refresh_token);
      await refreshUser();
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen scroll>
      <Header title={t('auth.forgotTitle')} showBack />

      {step === 'phone' ? (
        <>
          <TextField
            label={t('auth.phone')}
            value={phone}
            onChangeText={setPhone}
            keyboardType="phone-pad"
            placeholder={t('auth.phonePlaceholder')}
          />
          {error ? <Text style={styles.errorText}>{error}</Text> : null}
          <Button title={t('auth.sendCode')} onPress={handleSendOtp} loading={loading} />
        </>
      ) : (
        <>
          {info ? <Text style={styles.infoText}>{info}</Text> : null}
          <TextField label={t('auth.otpCode')} value={otp} onChangeText={setOtp} keyboardType="number-pad" placeholder="123456" />
          <TextField label={t('auth.newPassword')} value={newPassword} onChangeText={setNewPassword} secureTextEntry placeholder={t('auth.passwordMinHint')} />
          {error ? <Text style={styles.errorText}>{error}</Text> : null}
          <Button title={t('auth.resetPassword')} onPress={handleReset} loading={loading} />
        </>
      )}

      <Button title={t('common.back')} variant="secondary" onPress={() => navigation.goBack()} style={{ marginTop: spacing.sm }} />
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
  infoText: {
    color: colors.turquoise,
    fontSize: 13,
    marginBottom: spacing.md,
  },
});
