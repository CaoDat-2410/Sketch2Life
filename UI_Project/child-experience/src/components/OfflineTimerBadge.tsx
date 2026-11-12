import React from 'react'
import { View, Text, StyleSheet } from 'react-native'

export function OfflineTimerBadge({ seconds }: { seconds: number }) {
  const min = Math.floor(seconds / 60)
  const sec = seconds % 60
  return (
    <View style={styles.badge}>
      <Text style={styles.text}>⏱ {min}:{sec < 10 ? '0' : ''}{sec}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  badge: { backgroundColor: '#FDF2F8', paddingVertical: 8, paddingHorizontal: 16, borderRadius: 14 },
  text: { color: '#BE185D', fontWeight: 'bold', fontSize: 16 },
})
