import React, { useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radius, spacing } from '../theme/colors';
import { TextField } from './TextField';
import { Button } from './Button';
import { extractErrorMessage } from '../api/client';
import { useLanguage } from '../i18n/LanguageContext';

interface ReviewModalProps {
  visible: boolean;
  onClose: () => void;
  onSubmit: (rating: number, comment?: string) => Promise<void>;
}

export function ReviewModal({ visible, onClose, onSubmit }: ReviewModalProps) {
  const { t } = useLanguage();
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit(rating, comment.trim() || undefined);
      setComment('');
      setRating(5);
    } catch (e) {
      setError(extractErrorMessage(e, t('review.error')));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <Text style={styles.title}>{t('review.title')}</Text>
          <View style={styles.starsRow}>
            {[1, 2, 3, 4, 5].map((n) => (
              <Pressable key={n} onPress={() => setRating(n)} hitSlop={6}>
                <Text style={[styles.star, n <= rating && styles.starActive]}>★</Text>
              </Pressable>
            ))}
          </View>
          <TextField placeholder={t('review.commentPlaceholder')} value={comment} onChangeText={setComment} multiline />
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <Button title={t('review.submit')} onPress={handleSubmit} loading={submitting} />
          <Button title={t('review.later')} variant="secondary" onPress={onClose} style={{ marginTop: spacing.sm }} />
        </View>
      </View>
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
  starsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  star: {
    fontSize: 32,
    color: colors.border,
  },
  starActive: {
    color: colors.warning,
  },
  error: {
    color: colors.danger,
    fontSize: 12,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
});
