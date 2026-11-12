import React from 'react'
import { View, Pressable, StyleSheet } from 'react-native'

export function ColorPalettePicker({ colors, selected, onSelect }: { colors: string[]; selected: string; onSelect: (c: string) => void }) {
  return (
    <View style={styles.row}>
      {colors.map((c) => (
        <Pressable
          key={c}
          style={[styles.dot, { backgroundColor: c }, selected === c && styles.dotActive]}
          onPress={() => onSelect(c)}
        />
      ))}
    </View>
  )
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', gap: 10 },
  dot: { width: 36, height: 36, borderRadius: 18, borderWidth: 3, borderColor: 'transparent' },
  dotActive: { borderColor: '#0F172A', transform: [{ scale: 1.15 }] },
})
