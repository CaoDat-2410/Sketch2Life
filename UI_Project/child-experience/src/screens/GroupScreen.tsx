import React from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export function GroupScreen({ onOpenDraw, onExhibition }: { onOpenDraw: () => void; onExhibition: () => void }) {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>🌱 Khu vườn nhóm chung của chúng mình</Text>
        <View style={styles.navRow}>
          <Pressable style={styles.navBtn} onPress={onOpenDraw}><Text style={styles.navBtnText}>Bàn vẽ của con</Text></Pressable>
          <Pressable style={[styles.navBtn, styles.accentBtn]} onPress={onExhibition}><Text style={styles.accentBtnText}>Triển lãm 🎨</Text></Pressable>
        </View>
      </View>
      <View style={styles.gardenBoard}>
        <Text style={styles.gardenNotice}>Mây đã thêm hoa cúc vàng 🌼  •  Lá đã thêm nhánh lá xanh 🍃  •  Nắng đã thêm ông mặt trời ☀️</Text>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#ECFDF5', padding: 20 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#065F46' },
  navRow: { flexDirection: 'row', gap: 12 },
  navBtn: { paddingVertical: 10, paddingHorizontal: 18, borderRadius: 16, backgroundColor: '#D1FAE5' },
  navBtnText: { color: '#065F46', fontWeight: 'bold' },
  accentBtn: { backgroundColor: '#059669' },
  accentBtnText: { color: '#FFF', fontWeight: 'bold' },
  gardenBoard: { flex: 1, backgroundColor: '#FFF', borderRadius: 24, borderWidth: 2, borderColor: '#A7F3D0', justifyContent: 'center', alignItems: 'center' },
  gardenNotice: { color: '#047857', fontSize: 16, fontWeight: '600' },
})
