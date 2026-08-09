import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { CompositeNavigationProp, useNavigation } from '@react-navigation/native';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ModuleTile } from '../../components/ModuleTile';
import { NotificationBell } from '../../components/NotificationBell';
import { colors, spacing } from '../../theme/colors';
import { useAuth } from '../../context/AuthContext';
import { ClientStackParamList, ClientTabParamList } from '../../navigation/types';
import { useLanguage } from '../../i18n/LanguageContext';
import { TranslationKey } from '../../i18n';

type Nav = CompositeNavigationProp<
  BottomTabNavigationProp<ClientTabParamList, 'Home'>,
  NativeStackNavigationProp<ClientStackParamList>
>;

type TFn = (key: TranslationKey) => string;

function buildModules(t: TFn): Array<{
  key: string;
  title: string;
  icon: string;
  deep: string;
  accent: string;
  action: (nav: Nav) => void;
}> {
  return [
    {
      key: 'taxi',
      title: t('home.moduleTaxi'),
      icon: '🚕',
      deep: colors.module.taxi.deep,
      accent: colors.module.taxi.accent,
      action: (nav) => nav.navigate('TaxiOrder'),
    },
    {
      key: 'wedding',
      title: t('home.moduleWedding'),
      icon: '💍',
      deep: colors.module.wedding.deep,
      accent: colors.module.wedding.accent,
      action: (nav) => nav.navigate('WeddingRequest'),
    },
    {
      key: 'driver',
      title: t('home.modulePersonalDriver'),
      icon: '🧑‍✈️',
      deep: colors.module.driver.deep,
      accent: colors.module.driver.accent,
      action: (nav) => nav.navigate('PersonalDriver'),
    },
    {
      key: 'bus',
      title: t('home.moduleBus'),
      icon: '🚌',
      deep: colors.module.bus.deep,
      accent: colors.module.bus.accent,
      action: (nav) => nav.navigate('BusBooking'),
    },
    {
      key: 'gift',
      title: t('home.moduleGift'),
      icon: '🎁',
      deep: colors.module.gift.deep,
      accent: colors.module.gift.accent,
      action: (nav) => nav.navigate('GiftMemorial'),
    },
    {
      key: 'heavy',
      title: t('home.moduleHeavy'),
      icon: '🏗️',
      deep: colors.module.heavy.deep,
      accent: colors.module.heavy.accent,
      action: (nav) => nav.navigate('HeavyEquipment'),
    },
  ];
}

export function ClientHomeScreen() {
  const navigation = useNavigation<Nav>();
  const { user } = useAuth();
  const { t } = useLanguage();
  const modules = buildModules(t);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>{t('home.greetingClient')}</Text>
            <Text style={styles.name}>{user?.full_name || t('home.defaultClientName')}</Text>
          </View>
          <NotificationBell onPress={() => navigation.navigate('Notifications')} />
        </View>

        <View style={styles.grid}>
          {modules.map((m) => (
            <ModuleTile
              key={m.key}
              title={m.title}
              icon={m.icon}
              deepColor={m.deep}
              accentColor={m.accent}
              onPress={() => m.action(navigation)}
            />
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.paper,
  },
  content: {
    padding: spacing.lg,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  greeting: {
    fontSize: 14,
    color: colors.textMuted,
  },
  name: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.text,
    marginTop: 2,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    justifyContent: 'space-between',
  },
});
