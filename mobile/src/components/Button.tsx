import React from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, ViewStyle } from 'react-native';
import { colors, radius } from '../theme/colors';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  disabled?: boolean;
  loading?: boolean;
  style?: ViewStyle;
  accent?: string;
}

export function Button({ title, onPress, variant = 'primary', disabled, loading, style, accent }: ButtonProps) {
  const isDisabled = disabled || loading;
  const bg =
    variant === 'primary' ? accent ?? colors.deep : variant === 'danger' ? colors.danger : 'transparent';
  const border = variant === 'outline' ? colors.border : 'transparent';
  const textColor = variant === 'outline' || variant === 'secondary' ? colors.deep : '#FFFFFF';

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.base,
        { backgroundColor: variant === 'secondary' ? colors.paper : bg, borderColor: border, borderWidth: variant === 'outline' ? 1 : 0 },
        isDisabled && styles.disabled,
        pressed && !isDisabled && styles.pressed,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={textColor} />
      ) : (
        <Text style={[styles.text, { color: textColor }]}>{title}</Text>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    paddingVertical: 15,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 52,
  },
  text: {
    fontSize: 16,
    fontWeight: '700',
  },
  disabled: {
    opacity: 0.5,
  },
  pressed: {
    opacity: 0.85,
  },
});
