import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { colors, radius, shadows } from '../../theme';

export interface DiaryCardProps {
  title?: string;
  onPress?: () => void;
}

export const DiaryCard: React.FC<DiaryCardProps> = ({ title, onPress }) => {
  return (
    <TouchableOpacity activeOpacity={0.85} onPress={onPress} style={styles.card}>
      <Text style={styles.title}>{title || 'DiaryCard'}</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    padding: 14,
    marginVertical: 6,
    ...shadows.card,
  },
  title: { fontSize: 14, fontWeight: '700', color: colors.textHeading },
});
