import React from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radius, spacing } from '../theme/colors';
import { useLanguage } from '../i18n/LanguageContext';
import { Language } from '../i18n';

const OPTIONS: Array<{ code: Language; label: string; flag: string }> = [
  { code: 'uz', label: "O'zbekcha", flag: '🇺🇿' },
  { code: 'ru', label: 'Русский', flag: '🇷🇺' },
  { code: 'en', label: 'English', flag: '🇬🇧' },
];

interface LanguageModalProps {
  visible: boolean;
  onClose: () => void;
}

export function LanguageModal({ visible, onClose }: LanguageModalProps) {
  const { language, setLanguage, t } = useLanguage();

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.overlay} onPress={onClose}>
        <Pressable style={styles.card} onPress={(e) => e.stopPropagation()}>
          <Text style={styles.title}>{t('language.title')}</Text>
          {OPTIONS.map((opt) => (
            <Pressable
              key={opt.code}
              style={[styles.option, language === opt.code && styles.optionActive]}
              onPress={() => {
                setLanguage(opt.code);
                onClose();
              }}
            >
              <Text style={styles.flag}>{opt.flag}</Text>
              <Text style={[styles.optionText, language === opt.code && styles.optionTextActive]}>
                {opt.label}
              </Text>
              {language === opt.code ? <Text style={styles.check}>✓</Text> : null}
            </Pressable>
          ))}
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(15,42,56,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  card: {
    width: '100%',
    maxWidth: 360,
    backgroundColor: '#FFFFFF',
    borderRadius: radius.lg,
    padding: spacing.lg,
  },
  title: {
    fontSize: 17,
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: 13,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    marginBottom: spacing.xs,
  },
  optionActive: {
    backgroundColor: colors.paper,
  },
  flag: {
    fontSize: 20,
  },
  optionText: {
    flex: 1,
    fontSize: 15,
    color: colors.text,
    fontWeight: '600',
  },
  optionTextActive: {
    color: colors.deep,
    fontWeight: '800',
  },
  check: {
    fontSize: 16,
    color: colors.turquoise,
    fontWeight: '800',
  },
});
