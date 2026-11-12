import React from 'react'
import { View, Text, StyleSheet } from 'react-native'

export function Footnote() {
  return (
    <View style={styles.wrap}>
      <Text style={styles.note}>🌿 Không gian sáng tạo tự nhiên theo phương pháp Montessori</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: { paddingVertical: 8, alignItems: 'center' },
  note: { fontSize: 12, color: '#94A3B8' },
})
