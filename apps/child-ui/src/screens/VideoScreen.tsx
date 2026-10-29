import React from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export function VideoScreen({ onComplete }: { onComplete: () => void }) {
  return (
    <View style={styles.container}>
      <View style={styles.box}>
        <Text style={styles.clapper}>🎬</Text>
        <Text style={styles.title}>Đang tạo video hoạt hình...</Text>
        <Text style={styles.desc}>Trí tuệ nhân tạo đang biến nét vẽ chiếc lá và nụ hoa của con thành thước phim chuyển động!</Text>
        <View style={styles.progressTrack}><View style={styles.progressBar} /></View>
        <Pressable style={styles.nextBtn} onPress={onComplete}>
          <Text style={styles.nextBtnText}>Hoạt động sáng tạo ngoài màn hình ➜</Text>
        </Pressable>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAF5FF', justifyContent: 'center', alignItems: 'center' },
  box: { width: 540, backgroundColor: '#FFF', borderRadius: 32, padding: 36, alignItems: 'center', borderWidth: 2, borderColor: '#E9D5FF' },
  clapper: { fontSize: 48, marginBottom: 16 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#6B21A8', marginBottom: 10 },
  desc: { fontSize: 15, color: '#7E22CE', textAlign: 'center', lineHeight: 22, marginBottom: 24 },
  progressTrack: { width: '80%', height: 12, backgroundColor: '#F3E8FF', borderRadius: 6, overflow: 'hidden', marginBottom: 28 },
  progressBar: { width: '75%', height: '100%', backgroundColor: '#9333EA', borderRadius: 6 },
  nextBtn: { backgroundColor: '#9333EA', paddingVertical: 14, paddingHorizontal: 28, borderRadius: 20 },
  nextBtnText: { color: '#FFF', fontWeight: 'bold', fontSize: 16 },
})
