import React from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export function LearnScreen({ onNextVideo }: { onNextVideo: () => void }) {
  const steps = [
    { num: '1', title: 'Hạt mầm nảy mầm', desc: 'Uống nước mát trong đất ẩm' },
    { num: '2', title: 'Lá đón ánh nắng', desc: 'Quang hợp tạo diệp lục xanh tươi' },
    { num: '3', title: 'Hoa nở khoe sắc', desc: 'Tạo mật ngọt cho ong và bướm' },
  ]

  return (
    <View style={styles.container}>
      <Text style={styles.header}>🌱 3 bước sinh trưởng của cây cối</Text>
      <View style={styles.stepRow}>
        {steps.map((s) => (
          <View key={s.num} style={styles.stepCard}>
            <View style={styles.badge}><Text style={styles.badgeText}>{s.num}</Text></View>
            <Text style={styles.stepTitle}>{s.title}</Text>
            <Text style={styles.stepDesc}>{s.desc}</Text>
          </View>
        ))}
      </View>
      <Pressable style={styles.videoBtn} onPress={onNextVideo}>
        <Text style={styles.videoBtnText}>Xem phim hoạt hình của bé 🎬</Text>
      </Pressable>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0FDFA', padding: 24, alignItems: 'center' },
  header: { fontSize: 24, fontWeight: 'bold', color: '#115E59', marginBottom: 24 },
  stepRow: { flexDirection: 'row', gap: 20, marginBottom: 28 },
  stepCard: { width: 220, padding: 20, backgroundColor: '#FFF', borderRadius: 20, borderWidth: 2, borderColor: '#99F6E4', alignItems: 'center' },
  badge: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#0D9488', justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  badgeText: { color: '#FFF', fontWeight: 'bold', fontSize: 18 },
  stepTitle: { fontSize: 17, fontWeight: 'bold', color: '#134E4A', marginBottom: 6 },
  stepDesc: { fontSize: 13, color: '#0F766E', textAlign: 'center' },
  videoBtn: { backgroundColor: '#0D9488', paddingVertical: 16, paddingHorizontal: 36, borderRadius: 22 },
  videoBtnText: { color: '#FFF', fontSize: 17, fontWeight: 'bold' },
})
