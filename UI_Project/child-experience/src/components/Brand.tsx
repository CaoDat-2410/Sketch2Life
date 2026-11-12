import React from 'react'
import { View, Text, StyleSheet } from 'react-native'

export function Brand({ large = false }: { large?: boolean }) {
  return (
    <View style={styles.row}>
      <Text style={styles.icon}>🌱</Text>
      <Text style={[styles.text, large && styles.textLarge]}>Sketch2Life Kids</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  icon: { fontSize: 24 },
  text: { fontSize: 18, fontWeight: 'bold', color: '#0F172A' },
  textLarge: { fontSize: 24 },
})
