import React from 'react'
import { View, Pressable, StyleSheet } from 'react-native'

export function BrushSizeSlider({ current, onChange }: { current: number; onChange: (size: number) => void }) {
  const sizes = [3, 6, 12, 20]
  return (
    <View style={styles.wrap}>
      {sizes.map((s) => (
        <Pressable
          key={s}
          style={[styles.btn, current === s && styles.btnActive]}
          onPress={() => onChange(s)}
        >
          <View style={[styles.circle, { width: s * 1.5, height: s * 1.5, borderRadius: (s * 1.5) / 2 }]} />
        </Pressable>
      ))}
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  btn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#F1F5F9', justifyContent: 'center', alignItems: 'center' },
  btnActive: { backgroundColor: '#DBEAFE', borderWidth: 2, borderColor: '#1685F8' },
  circle: { backgroundColor: '#334155' },
})
