import React from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export interface TopBarProps {
  screen: string
  name: string
  onBack: () => void
  onOffline: () => void
}

export function TopBar({ screen: _screen, name, onBack, onOffline }: TopBarProps) {
  return (
    <View style={styles.bar}>
      <Pressable style={styles.backBtn} onPress={onBack}>
        <Text style={styles.backText}>◀ Quay lại</Text>
      </Pressable>
      <Text style={styles.title}>Sketch2Life • Bạn {name}</Text>
      <Pressable style={styles.offlineBtn} onPress={onOffline}>
        <Text style={styles.offlineText}>📡 Mất mạng</Text>
      </Pressable>
    </View>
  )
}

const styles = StyleSheet.create({
  bar: { height: 56, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, backgroundColor: '#FFF', borderBottomWidth: 1, borderColor: '#E2E8F0' },
  backBtn: { padding: 8 },
  backText: { color: '#1685F8', fontWeight: 'bold' },
  title: { fontSize: 16, fontWeight: 'bold', color: '#1E293B' },
  offlineBtn: { padding: 8, backgroundColor: '#FEE2E2', borderRadius: 12 },
  offlineText: { color: '#DC2626', fontWeight: '600', fontSize: 12 },
})
