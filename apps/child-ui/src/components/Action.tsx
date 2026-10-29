import React from 'react'
import { Pressable, Text, StyleSheet, ViewStyle } from 'react-native'

export interface ActionProps {
  label: string
  icon?: string
  onPress: () => void
  kind?: 'primary' | 'secondary' | 'pink' | 'yellow'
  style?: ViewStyle
  compact?: boolean
}

export function Action({ label, icon, onPress, kind = 'primary', style, compact = false }: ActionProps) {
  const buttonStyle = kind === 'primary' ? styles.primary : kind === 'pink' ? styles.pink : kind === 'yellow' ? styles.yellow : styles.secondary
  const textStyle = kind === 'primary' ? styles.textLight : kind === 'pink' ? styles.textPink : kind === 'yellow' ? styles.textYellow : styles.textDark

  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [styles.action, compact && styles.compact, buttonStyle, style, pressed && styles.pressed]}
    >
      <Text style={[styles.label, compact && styles.labelCompact, textStyle]}>
        {icon ? `${icon}  ` : ''}{label}
      </Text>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  action: { minHeight: 48, borderRadius: 18, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 20 },
  compact: { minHeight: 40, paddingHorizontal: 14 },
  primary: { backgroundColor: '#1685F8' },
  secondary: { backgroundColor: '#F1F5F9' },
  pink: { backgroundColor: '#FCE7F3' },
  yellow: { backgroundColor: '#FEF08A' },
  textLight: { color: '#FFF', fontWeight: 'bold' },
  textDark: { color: '#1E293B', fontWeight: '600' },
  textPink: { color: '#DB2777', fontWeight: 'bold' },
  textYellow: { color: '#854D0E', fontWeight: 'bold' },
  label: { fontSize: 16 },
  labelCompact: { fontSize: 14 },
  pressed: { opacity: 0.8 },
})
