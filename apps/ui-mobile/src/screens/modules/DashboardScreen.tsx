import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { colors, radius, shadows } from '../../theme';
import type { ScreenId } from '../../types';

export interface DashboardScreenProps {
  onNavigate?: (screen: ScreenId) => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ onNavigate }) => {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>DashboardScreen</Text>
      <Text style={styles.subtitle}>Sketch2Life Modular Screen Component</Text>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: 20, alignItems: 'center' },
  title: { fontSize: 20, fontWeight: 'bold', color: colors.textHeading },
  subtitle: { fontSize: 13, color: colors.textSoft, marginTop: 6 },
});
