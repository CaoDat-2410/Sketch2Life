import React from 'react'
import { Pressable, Text, StyleSheet } from 'react-native'

export function FeelingCard({ emoji, label, selected, onSelect }: { emoji: string; label: string; selected: boolean; onSelect: () => void }) {
  return (
    <Pressable style={[styles.card, selected && styles.active]} onPress={onSelect}>
      <Text style={styles.emoji}>{emoji}</Text>
      <Text style={styles.label}>{label}</Text>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  card: { width: 100, height: 110, borderRadius: 20, backgroundColor: '#FFF', justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: '#E2E8F0' },
  active: { borderColor: '#F59E0B', backgroundColor: '#FEF3C7' },
  emoji: { fontSize: 36, marginBottom: 6 },
  label: { fontSize: 14, fontWeight: 'bold', color: '#1E293B' },
})
