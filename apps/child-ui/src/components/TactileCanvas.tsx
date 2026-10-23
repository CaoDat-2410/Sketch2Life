import React from 'react'
import { View, StyleSheet } from 'react-native'

export function TactileCanvas({ children }: { children?: React.ReactNode }) {
  return <View style={styles.canvas}>{children}</View>
}

const styles = StyleSheet.create({
  canvas: { flex: 1, backgroundColor: '#FFF', borderRadius: 24, overflow: 'hidden' },
})
