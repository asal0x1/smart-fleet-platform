import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, radius, spacing } from '../theme/colors';
import { Button } from './Button';

interface Props {
  children: React.ReactNode;
}

interface State {
  error: Error | null;
}

// Ilovaning istalgan joyida kutilmagan render xatosi butun ekranni
// qulatib, oq/qora ekran qoldirmasligi uchun umumiy tutqich.
export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary tutdi:', error, info.componentStack);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (this.state.error) {
      return (
        <View style={styles.wrap}>
          <Text style={styles.icon}>⚠️</Text>
          <Text style={styles.title}>Kutilmagan xatolik yuz berdi</Text>
          <Text style={styles.message}>{this.state.error.message || "Noma'lum xatolik"}</Text>
          <Button title="Qayta urinish" onPress={this.reset} style={{ marginTop: spacing.lg }} />
        </View>
      );
    }
    return this.props.children;
  }
}

const styles = StyleSheet.create({
  wrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.paper,
    padding: spacing.xl,
  },
  icon: {
    fontSize: 48,
    marginBottom: spacing.md,
  },
  title: {
    fontSize: 18,
    fontWeight: '800',
    color: colors.text,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  message: {
    fontSize: 13,
    color: colors.textMuted,
    textAlign: 'center',
    backgroundColor: '#FFFFFF',
    padding: spacing.md,
    borderRadius: radius.md,
  },
});
