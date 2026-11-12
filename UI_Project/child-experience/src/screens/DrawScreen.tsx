import React, { useState } from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export interface DrawScreenProps {
  onIdeas: () => void
  onReview: () => void
  onGroup: () => void
}

export function DrawScreen({ onIdeas, onReview, onGroup }: DrawScreenProps) {
  const [color, setColor] = useState('#1685F8')
  const [tool, setTool] = useState<'pen' | 'eraser'>('pen')
  const palette = ['#FFD21F', '#FF596C', '#1685F8', '#31C978', '#9250E8', '#111827']

  return (
    <View style={styles.container}>
      <View style={styles.sidebar}>
        <Text style={styles.panelTitle}>🎨 Hộp màu</Text>
        {palette.map((c) => (
          <Pressable
            key={c}
            style={[styles.swatch, { backgroundColor: c }, color === c && tool === 'pen' && styles.swatchActive]}
            onPress={() => { setColor(c); setTool('pen') }}
          />
        ))}
        <Pressable
          style={[styles.toolBtn, tool === 'eraser' && styles.toolBtnActive]}
          onPress={() => setTool('eraser')}
        >
          <Text style={styles.toolIcon}>🧹 Tẩy</Text>
        </Pressable>
      </View>
      <View style={styles.canvasArea}>
        <View style={styles.canvasSurface}>
          <Text style={styles.watermark}>Bàn vẽ cảm ứng của bé</Text>
        </View>
        <View style={styles.toolbar}>
          <Pressable style={styles.navBtn} onPress={onIdeas}><Text style={styles.navBtnText}>💡 Gợi ý</Text></Pressable>
          <Pressable style={styles.navBtn} onPress={onGroup}><Text style={styles.navBtnText}>🍃 Vườn nhóm</Text></Pressable>
          <Pressable style={[styles.navBtn, styles.reviewBtn]} onPress={onReview}><Text style={styles.reviewBtnText}>Gửi cô duyệt ✓</Text></Pressable>
        </View>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, flexDirection: 'row', backgroundColor: '#F8FAFC' },
  sidebar: { width: 110, padding: 12, backgroundColor: '#FFF', borderRightWidth: 1, borderColor: '#E2E8F0', alignItems: 'center' },
  panelTitle: { fontSize: 13, fontWeight: '700', color: '#64748B', marginBottom: 12 },
  swatch: { width: 44, height: 44, borderRadius: 22, marginVertical: 6, borderWidth: 3, borderColor: 'transparent' },
  swatchActive: { borderColor: '#0F172A', transform: [{ scale: 1.1 }] },
  toolBtn: { marginTop: 12, paddingVertical: 10, paddingHorizontal: 12, borderRadius: 14, backgroundColor: '#F1F5F9' },
  toolBtnActive: { backgroundColor: '#FEE2E2', borderWidth: 2, borderColor: '#EF4444' },
  toolIcon: { fontSize: 14, fontWeight: 'bold' },
  canvasArea: { flex: 1, padding: 16 },
  canvasSurface: { flex: 1, backgroundColor: '#FFF', borderRadius: 24, borderWidth: 2, borderColor: '#E2E8F0', justifyContent: 'center', alignItems: 'center' },
  watermark: { color: '#CBD5E1', fontSize: 18, fontWeight: '600' },
  toolbar: { flexDirection: 'row', justifyContent: 'flex-end', gap: 12, marginTop: 12 },
  navBtn: { paddingVertical: 12, paddingHorizontal: 20, borderRadius: 16, backgroundColor: '#E2E8F0' },
  navBtnText: { fontWeight: '600', color: '#334155' },
  reviewBtn: { backgroundColor: '#1685F8' },
  reviewBtnText: { color: '#FFF', fontWeight: 'bold' },
})
