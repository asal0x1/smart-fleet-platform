import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Screen } from '../../components/Screen';
import { TextField } from '../../components/TextField';
import { Button } from '../../components/Button';
import { Header } from '../../components/Header';
import { colors, radius, spacing } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';
import { extractErrorMessage } from '../../api/client';
import { AuthStackParamList } from '../../navigation/types';
import { isValidUzPhone, normalizePhone } from '../../utils/phone';
import { Role } from '../../types';
import { useLanguage } from '../../i18n/LanguageContext';

type Props = NativeStackScreenProps<AuthStackParamList, 'Register'>;

export function RegisterScreen({ navigation }: Props) {
  const { t } = useLanguage();
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('+998');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Role>('client');
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
      await register(normalizePhone(phone), password, role, fullName.trim() || undefined);
    } catch (e) {
      setError(extractErrorMessage(e, t('auth.registerError')));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen scroll>
      <Header title={t('auth.registerTitle')} showBack />

      <View style={styles.roleRow}>
        <RoleOption label={t('auth.roleClient')} selected={role === 'client'} onPress={() => setRole('client')} />
        <RoleOption label={t('auth.roleDriver')} selected={role === 'driver'} onPress={() => setRole('driver')} />
      </View>

      <TextField label={t('auth.fullName')} value={fullName} onChangeText={setFullName} placeholder={t('auth.fullNamePlaceholder')} />
      <TextField
        label={t('auth.phone')}
        value={phone}
        onChangeText={setPhone}
        keyboardType="phone-pad"
        placeholder={t('auth.phonePlaceholder')}
        autoCapitalize="none"
      />
      <TextField label={t('auth.password')} value={password} onChangeText={setPassword} secureTextEntry placeholder={t('auth.passwordMinHint')} />

      {error ? <Text style={styles.errorText}>{error}</Text> : null}

      <Button title={t('auth.register')} onPress={onSubmit} loading={loading} style={{ marginTop: spacing.sm }} />
      <Button title={t('common.back')} variant="secondary" onPress={() => navigation.goBack()} style={{ marginTop: spacing.sm }} />
    </Screen>
  );
}

function RoleOption({ label, selected, onPress }: { label: string; selected: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[styles.roleOption, selected && styles.roleOptionSelected]}>
      <Text style={[styles.roleText, selected && styles.roleTextSelected]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  roleRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  roleOption: {
    flex: 1,
    paddingVertical: 13,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  roleOptionSelected: {
    backgroundColor: colors.deep,
    borderColor: colors.deep,
  },
  roleText: {
    fontWeight: '700',
    color: colors.text,
  },
  roleTextSelected: {
    color: '#FFFFFF',
  },
  errorText: {
    color: colors.danger,
    fontSize: 13,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
});
