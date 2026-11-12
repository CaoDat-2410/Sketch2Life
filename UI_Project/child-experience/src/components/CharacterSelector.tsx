import React from 'react'
import { View, Text, Pressable, StyleSheet } from 'react-native'

export function CharacterSelector({ value, onChange }: { value: string; onChange: (name: string) => void }) {
  const characters = [
    { name: 'Mây', icon: '☁️' },
    { name: 'Lá', icon: '🍃' },
  ]
  return (
    <View style={styles.row}>
      {characters.map((c) => (
        <Pressable
          key={c.name}
          style={[styles.item, value === c.name && styles.itemActive]}
          onPress={() => onChange(c.name)}
        >
          <Text style={styles.icon}>{c.icon}</Text>
          <Text style={styles.name}>{c.name}</Text>
        </Pressable>
      ))}
    </View>
  )
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', gap: 16 },
  item: { padding: 14, borderRadius: 20, backgroundColor: '#F8FAFC', borderWidth: 2, borderColor: '#E2E8F0', alignItems: 'center' },
  itemActive: { borderColor: '#1685F8', backgroundColor: '#EFF6FF' },
  icon: { fontSize: 28, marginBottom: 4 },
  name: { fontSize: 14, fontWeight: 'bold' },
})
