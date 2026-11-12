import React from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export function ReviewScreen({ onReturnToDraw, onGoToGroup }: { onReturnToDraw: () => void; onGoToGroup: () => void }) {
  return (
    <View style={styles.container}>
      <View style={styles.modalCard}>
        <Text style={styles.statusBadge}>Đang chờ duyệt Gate A</Text>
        <Text style={styles.title}>Cô/thầy giáo đang xem tranh của con!</Text>
        <Text style={styles.desc}>Bức tranh chiếc lá sinh học của con rất đáng yêu. Sau khi được duyệt, tranh sẽ xuất hiện trong vườn chung của cả lớp.</Text>
        <View style={styles.btnRow}>
          <Pressable style={styles.btnSecondary} onPress={onReturnToDraw}>
            <Text style={styles.btnSecondaryText}>Vẽ thêm chi tiết</Text>
          </Pressable>
          <Pressable style={styles.btnPrimary} onPress={onGoToGroup}>
            <Text style={styles.btnPrimaryText}>Xem vườn nhóm ➜</Text>
          </Pressable>
        </View>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F1F5F9', justifyContent: 'center', alignItems: 'center' },
  modalCard: { width: 520, backgroundColor: '#FFF', borderRadius: 28, padding: 32, alignItems: 'center' },
  statusBadge: { backgroundColor: '#FEF3C7', color: '#B45309', paddingVertical: 6, paddingHorizontal: 16, borderRadius: 14, fontWeight: 'bold', marginBottom: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: '#0F172A', marginBottom: 10, textAlign: 'center' },
  desc: { fontSize: 15, color: '#64748B', textAlign: 'center', lineHeight: 22, marginBottom: 28 },
  btnRow: { flexDirection: 'row', gap: 16 },
  btnSecondary: { paddingVertical: 14, paddingHorizontal: 24, borderRadius: 18, backgroundColor: '#E2E8F0' },
  btnSecondaryText: { color: '#334155', fontWeight: 'bold' },
  btnPrimary: { paddingVertical: 14, paddingHorizontal: 28, borderRadius: 18, backgroundColor: '#1685F8' },
  btnPrimaryText: { color: '#FFF', fontWeight: 'bold' },
})
