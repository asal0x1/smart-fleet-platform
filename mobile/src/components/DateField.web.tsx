import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, radius, spacing } from '../theme/colors';
import { formatDateForApi } from '../utils/date';

interface DateFieldProps {
  label: string;
  value: Date | null;
  onChange: (date: Date) => void;
  mode: 'date' | 'time';
  minimumDate?: Date;
}

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const MINUTES = Array.from({ length: 12 }, (_, i) => i * 5); // 5 daqiqalik qadam — tanlashni osonlashtiradi

const selectStyle: React.CSSProperties = {
  backgroundColor: '#FFFFFF',
  border: `1px solid ${colors.border}`,
  borderRadius: radius.md,
  padding: '13px 12px',
  fontSize: 15,
  color: colors.text,
  fontFamily: 'inherit',
  flex: 1,
  boxSizing: 'border-box',
};

// @react-native-community/datetimepicker'ning web varianti yo'q. Sana uchun
// brauzerning tabiiy <input type="date"> qulay ishlaydi. Vaqt uchun esa
// tabiiy <input type="time"> ba'zi brauzerlarda noqulay/tor bo'lgani uchun
// soat va daqiqani alohida oddiy tanlov ro'yxati (select) orqali beramiz —
// bir marta bosib tanlash, aylantirib o'tirish shart emas.
export function DateField({ label, value, onChange, mode, minimumDate }: DateFieldProps) {
  if (mode === 'time') {
    const hour = value ? value.getHours() : null;
    const minute = value ? value.getMinutes() : null;

    const applyTime = (h: number, m: number) => {
      const next = value ? new Date(value) : new Date();
      next.setHours(h, m, 0, 0);
      onChange(next);
    };

    return (
      <View style={styles.wrapper}>
        <Text style={styles.label}>{label}</Text>
        <View style={styles.timeRow}>
          {React.createElement(
            'select',
            {
              value: hour ?? '',
              onChange: (e: any) => applyTime(Number(e.target.value), minute ?? 0),
              style: selectStyle,
            },
            React.createElement('option', { value: '', disabled: true }, '--'),
            ...HOURS.map((h) => React.createElement('option', { key: h, value: h }, String(h).padStart(2, '0')))
          )}
          <Text style={styles.colon}>:</Text>
          {React.createElement(
            'select',
            {
              value: minute ?? '',
              onChange: (e: any) => applyTime(hour ?? 0, Number(e.target.value)),
              style: selectStyle,
            },
            React.createElement('option', { value: '', disabled: true }, '--'),
            ...MINUTES.map((m) => React.createElement('option', { key: m, value: m }, String(m).padStart(2, '0')))
          )}
        </View>
      </View>
    );
  }

  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      {React.createElement('input', {
        type: 'date',
        value: value ? formatDateForApi(value) : '',
        min: minimumDate ? formatDateForApi(minimumDate) : undefined,
        onChange: (e: any) => {
          const raw = e.target.value;
          if (!raw) return;
          const [y, m, d] = raw.split('-').map(Number);
          onChange(new Date(y, m - 1, d));
        },
        style: {
          backgroundColor: '#FFFFFF',
          border: `1px solid ${colors.border}`,
          borderRadius: radius.md,
          padding: '13px 16px',
          fontSize: 15,
          color: colors.text,
          fontFamily: 'inherit',
          width: '100%',
          boxSizing: 'border-box',
        },
      })}
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
  timeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  colon: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
  },
});
