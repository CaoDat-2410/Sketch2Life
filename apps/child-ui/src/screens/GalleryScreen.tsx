import React from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export function GalleryScreen({ onLearn, onDraw }: { onLearn: () => void; onDraw: () => void }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>🌻 Triển lãm khu vườn lớp học</Text>
      <Text style={styles.sub}>Bức tranh hoàn chỉnh sau khi ghép các nét vẽ của Mây, Lá và Nắng</Text>
      <View style={styles.galleryFrame}>
        <Text style={styles.speech}>Bác Cây: 'Các con đã tạo nên một khu vườn ngập tràn sức sống!'</Text>
      </View>
      <View style={styles.bottomBar}>
        <Pressable style={styles.btn} onPress={onDraw}><Text style={styles.btnText}>Quay lại vẽ</Text></Pressable>
        <Pressable style={[styles.btn, styles.primaryBtn]} onPress={onLearn}><Text style={styles.primaryBtnText}>Khám phá khoa học ➜</Text></Pressable>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FEF2F2', padding: 24, alignItems: 'center' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#991B1B', marginBottom: 6 },
  sub: { fontSize: 15, color: '#B91C1C', marginBottom: 20 },
  galleryFrame: { flex: 1, width: '100%', backgroundColor: '#FFF', borderRadius: 24, borderWidth: 2, borderColor: '#FECACA', justifyContent: 'center', alignItems: 'center' },
  speech: { fontSize: 18, fontWeight: '600', color: '#991B1B' },
  bottomBar: { flexDirection: 'row', gap: 16, marginTop: 16 },
  btn: { paddingVertical: 12, paddingHorizontal: 24, borderRadius: 16, backgroundColor: '#E2E8F0' },
  btnText: { fontWeight: 'bold', color: '#334155' },
  primaryBtn: { backgroundColor: '#DC2626' },
  primaryBtnText: { color: '#FFF', fontWeight: 'bold' },
})
