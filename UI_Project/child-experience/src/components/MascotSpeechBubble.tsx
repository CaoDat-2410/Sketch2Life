import React from 'react'
import { View, Text, StyleSheet } from 'react-native'

export function MascotSpeechBubble({ message }: { message: string }) {
  return (
    <View style={styles.bubble}>
      <Text style={styles.mascot}>🌿</Text>
      <Text style={styles.text}>{message}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  bubble: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#F0FDF4', padding: 14, borderRadius: 18, borderWidth: 1, borderColor: '#BBF7D0' },
  mascot: { fontSize: 24, marginRight: 10 },
  text: { fontSize: 14, fontWeight: '600', color: '#166534', flex: 1 },
})
