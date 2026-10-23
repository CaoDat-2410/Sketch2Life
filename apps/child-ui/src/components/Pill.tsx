import React from 'react'
import { View, Text, StyleSheet } from 'react-native'

export interface PillProps {
  children: React.ReactNode
  tone?: 'blue' | 'green' | 'pink' | 'yellow'
}

export function Pill({ children, tone = 'blue' }: PillProps) {
  const toneStyle = tone === 'green' ? styles.green : tone === 'pink' ? styles.pink : tone === 'yellow' ? styles.yellow : styles.blue
  const textTone = tone === 'green' ? styles.textGreen : tone === 'pink' ? styles.textPink : tone === 'yellow' ? styles.textYellow : styles.textBlue

  return (
    <View style={[styles.pill, toneStyle]}>
      <Text style={[styles.text, textTone]}>{children}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  pill: { paddingVertical: 6, paddingHorizontal: 14, borderRadius: 16 },
  blue: { backgroundColor: '#EFF6FF' },
  green: { backgroundColor: '#ECFDF5' },
  pink: { backgroundColor: '#FDF2F8' },
  yellow: { backgroundColor: '#FEFCE8' },
  text: { fontSize: 13, fontWeight: '700' },
  textBlue: { color: '#1D4ED8' },
  textGreen: { color: '#047857' },
  textPink: { color: '#BE185D' },
  textYellow: { color: '#A16207' },
})
