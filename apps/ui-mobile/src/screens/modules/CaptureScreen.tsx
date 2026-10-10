import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { colors, radius, shadows } from '../../theme';
import type { ScreenId } from '../../types';

export interface CaptureScreenProps {
  onNavigate?: (screen: ScreenId) => void;
}

export const CaptureScreen: React.FC<CaptureScreenProps> = ({ onNavigate }) => {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>CaptureScreen</Text>
      <Text style={styles.subtitle}>Sketch2Life Modular Screen Component</Text>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bgLight },
  content: { padding: 20, alignItems: 'center' },
  title: { fontSize: 20, fontWeight: 'bold', color: colors.textHeading },
  subtitle: { fontSize: 13, color: colors.textSoft, marginTop: 6 },
});
