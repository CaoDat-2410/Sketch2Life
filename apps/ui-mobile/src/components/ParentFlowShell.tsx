import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, shadows } from '../theme';

export const ParentFlowHeader: React.FC<{
  title: string;
  onBack?: () => void;
  action?: React.ReactNode;
}> = ({ title, onBack, action }) => (
  <View style={styles.header}>
    {onBack ? (
      <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" activeOpacity={0.78} onPress={onBack} style={styles.iconButton}>
        <Ionicons name="arrow-back" size={19} color={colors.textBody} />
      </TouchableOpacity>
    ) : <View style={styles.iconButton} />}
    <Text style={styles.headerTitle}>{title}</Text>
    {action || <View style={styles.iconButton} />}
  </View>
);

export const ParentFlowProgress: React.FC<{ label: string; percent: number }> = ({ label, percent }) => (
  <View style={styles.progressWrap} accessibilityLabel={label}>
    <View style={styles.progressTrack}><View style={[styles.progressFill, { width: `${Math.max(0, Math.min(100, percent))}%` }]} /></View>
    <Text style={styles.progressLabel}>{label}</Text>
  </View>
);

export const ParentFlowPrimary: React.FC<{
  label: string;
  onPress: () => void;
  disabled?: boolean;
}> = ({ label, onPress, disabled }) => (
  <TouchableOpacity accessibilityRole="button" disabled={disabled} activeOpacity={0.82} onPress={onPress} style={[styles.primary, disabled && styles.primaryDisabled]}>
    <Text style={styles.primaryText}>{label}</Text>
    <Ionicons name="arrow-forward" size={18} color={colors.white} />
  </TouchableOpacity>
);

export const ParentFlowNotice: React.FC<{
  children: React.ReactNode;
  icon?: keyof typeof Ionicons.glyphMap;
  tone?: 'blue' | 'green' | 'amber';
}> = ({ children, icon = 'information-circle-outline', tone = 'blue' }) => (
  <View style={[styles.notice, tone === 'green' ? styles.noticeGreen : tone === 'amber' ? styles.noticeAmber : styles.noticeBlue]}>
    <Ionicons name={icon} size={18} color={tone === 'green' ? colors.greenDeep : tone === 'amber' ? colors.yellowDeep : colors.blueDeep} />
    <Text style={styles.noticeText}>{children}</Text>
  </View>
);

export const ParentFlowScroll: React.FC<React.ComponentProps<typeof ScrollView>> = ({ children, contentContainerStyle, ...props }) => (
  <ScrollView {...props} contentContainerStyle={[styles.container, contentContainerStyle]} showsVerticalScrollIndicator={false}>{children}</ScrollView>
);

const styles = StyleSheet.create({
  container: { padding: 20, paddingBottom: 36, backgroundColor: '#F8FAFC', minHeight: '100%' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 22 },
  iconButton: { width: 42, height: 42, borderRadius: 16, backgroundColor: colors.white, borderWidth: 1, borderColor: '#F0E7D8', alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontSize: 16, fontWeight: '900', color: colors.textHeading },
  progressWrap: { marginBottom: 20 },
  progressTrack: { height: 7, borderRadius: 5, backgroundColor: '#E8EEF7', overflow: 'hidden' },
  progressFill: { height: 7, borderRadius: 5, backgroundColor: colors.blueDeep },
  progressLabel: { fontSize: 11, fontWeight: '800', color: colors.textSoft, marginTop: 8 },
  primary: { minHeight: 56, borderRadius: 18, backgroundColor: colors.blueDeep, borderBottomWidth: 4, borderBottomColor: '#1D4ED8', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 22, paddingHorizontal: 16, ...shadows.button },
  primaryDisabled: { backgroundColor: '#CBD5E1' },
  primaryText: { fontSize: 15, fontWeight: '900', color: colors.white },
  notice: { flexDirection: 'row', gap: 8, alignItems: 'flex-start', padding: 14, borderRadius: 18, marginTop: 15 },
  noticeBlue: { backgroundColor: '#EFF6FF' },
  noticeGreen: { backgroundColor: '#F0FDF4' },
  noticeAmber: { backgroundColor: '#FFFBEB' },
  noticeText: { flex: 1, fontSize: 11, lineHeight: 16, color: colors.textBody },
});

export const parentFlowStyles = styles;
