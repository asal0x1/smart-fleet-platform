import React, { useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { colors, radius, spacing } from '../theme/colors';
import { useLanguage } from '../i18n/LanguageContext';
import { Language } from '../i18n';

interface DateFieldProps {
  label: string;
  value: Date | null;
  onChange: (date: Date) => void;
  mode: 'date' | 'time';
  minimumDate?: Date;
}

const LOCALE_MAP: Record<Language, string> = {
  uz: 'uz-UZ',
  ru: 'ru-RU',
  en: 'en-US',
};

function format(value: Date, mode: 'date' | 'time', locale: string) {
  if (mode === 'date') {
    return value.toLocaleDateString(locale);
  }
  return value.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' });
}

export function DateField({ label, value, onChange, mode, minimumDate }: DateFieldProps) {
  const { t, language } = useLanguage();
  const [open, setOpen] = useState(false);
  const locale = LOCALE_MAP[language];

  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <Pressable style={styles.field} onPress={() => setOpen(true)}>
        <Text style={[styles.fieldText, !value && styles.placeholder]}>
          {value ? format(value, mode, locale) : mode === 'date' ? t('dateField.pickDate') : t('dateField.pickTime')}
        </Text>
      </Pressable>
      {open && (
        <DateTimePicker
          value={value ?? new Date()}
          mode={mode}
          minimumDate={minimumDate}
          display={Platform.OS === 'ios' ? 'spinner' : 'default'}
          onChange={(event, selected) => {
            setOpen(Platform.OS === 'ios');
            if (event.type === 'dismissed') {
              setOpen(false);
              return;
            }
            if (selected) onChange(selected);
            if (Platform.OS === 'android') setOpen(false);
          }}
        />
      )}
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
});
