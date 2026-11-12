import React from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export function OfflineScreen({ onFeelings }: { onFeelings: () => void }) {
  return (
    <View style={styles.container}>
      <View style={styles.banner}>
        <Text style={styles.tag}>🍃 Hoạt động thủ công Montessori</Text>
        <Text style={styles.title}>Thu thập lá rụng ngoài vườn để dán tranh</Text>
        <Text style={styles.desc}>Rời màn hình trong 10 phút. Con hãy cùng thầy cô và các bạn ra sân trường nhặt 3 chiếc lá rụng có hình dạng khác nhau nhé!</Text>
        <View style={styles.timerBadge}>
          <Text style={styles.timerText}>⏱ Thời gian trải nghiệm thực tế: 10:00</Text>
        </View>
        <Pressable style={styles.doneBtn} onPress={onFeelings}>
          <Text style={styles.doneBtnText}>Con đã hoàn thành ✓</Text>
        </Pressable>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FDF4FF', justifyContent: 'center', alignItems: 'center' },
  banner: { width: 560, backgroundColor: '#FFF', borderRadius: 28, padding: 32, alignItems: 'center', borderWidth: 2, borderColor: '#F5D0FE' },
  tag: { backgroundColor: '#FAE8FF', color: '#86198F', paddingVertical: 6, paddingHorizontal: 16, borderRadius: 12, fontWeight: 'bold', marginBottom: 12 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#701A75', textAlign: 'center', marginBottom: 10 },
  desc: { fontSize: 15, color: '#86198F', textAlign: 'center', lineHeight: 22, marginBottom: 20 },
  timerBadge: { backgroundColor: '#FDF2F8', paddingVertical: 10, paddingHorizontal: 20, borderRadius: 16, marginBottom: 24 },
  timerText: { color: '#BE185D', fontWeight: 'bold', fontSize: 15 },
  doneBtn: { backgroundColor: '#A21CAF', paddingVertical: 14, paddingHorizontal: 32, borderRadius: 20 },
  doneBtnText: { color: '#FFF', fontWeight: 'bold', fontSize: 16 },
})
