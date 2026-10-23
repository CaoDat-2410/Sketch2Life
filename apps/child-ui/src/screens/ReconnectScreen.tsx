import React from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export function ReconnectScreen({ onRetry, onTeacherHelp }: { onRetry: () => void; onTeacherHelp: () => void }) {
  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.wifiIcon}>📡</Text>
        <Text style={styles.title}>Mất kết nối mạng tạm thời!</Text>
        <Text style={styles.desc}>Đừng lo lắng nhé, tất cả nét vẽ của con đã được máy lưu lại an toàn.</Text>
        <View style={styles.btnRow}>
          <Pressable style={styles.retryBtn} onPress={onRetry}>
            <Text style={styles.retryBtnText}>⟳ Thử kết nối lại</Text>
          </Pressable>
          <Pressable style={styles.helpBtn} onPress={onTeacherHelp}>
            <Text style={styles.helpBtnText}>👩🏻‍🏫 Nhờ cô/thầy giúp</Text>
          </Pressable>
        </View>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC', justifyContent: 'center', alignItems: 'center' },
  card: { width: 500, backgroundColor: '#FFF', borderRadius: 28, padding: 32, alignItems: 'center', borderWidth: 2, borderColor: '#E2E8F0' },
  wifiIcon: { fontSize: 50, marginBottom: 12 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#0F172A', marginBottom: 8 },
  desc: { fontSize: 15, color: '#64748B', textAlign: 'center', lineHeight: 22, marginBottom: 28 },
  btnRow: { flexDirection: 'row', gap: 16 },
  retryBtn: { backgroundColor: '#1685F8', paddingVertical: 14, paddingHorizontal: 24, borderRadius: 18 },
  retryBtnText: { color: '#FFF', fontWeight: 'bold' },
  helpBtn: { backgroundColor: '#FCE7F3', paddingVertical: 14, paddingHorizontal: 24, borderRadius: 18 },
  helpBtnText: { color: '#DB2777', fontWeight: 'bold' },
})
