import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { Screen } from '../../components/Screen';
import { Header } from '../../components/Header';
import { colors, spacing } from '../../theme/colors';
import { ClientStackParamList } from '../../navigation/types';
import { useLanguage } from '../../i18n/LanguageContext';

type Props = NativeStackScreenProps<ClientStackParamList, 'ComingSoon'>;

export function ComingSoonScreen({ route }: Props) {
  const { t } = useLanguage();
  const { title, icon, description } = route.params;
  return (
    <Screen>
      <Header title={title} />
      <View style={styles.body}>
        <Text style={styles.icon}>{icon}</Text>
        <Text style={styles.title}>{t('comingSoon.title')}</Text>
        <Text style={styles.description}>{description}</Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  body: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.xl,
  },
  icon: {
    fontSize: 56,
    marginBottom: spacing.md,
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  description: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    lineHeight: 20,
  },
});
