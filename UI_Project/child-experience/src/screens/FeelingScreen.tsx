import React, { useState } from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export function FeelingScreen({ onSubmit }: { onSubmit: (feeling: string) => void }) {
  const [selected, setSelected] = useState('Vui vẻ')
  const feelings = [
    { label: 'Vui vẻ', emoji: '😊', color: '#FEF08A' },
    { label: 'Hào hứng', emoji: '🤩', color: '#BAE6FD' },
    { label: 'Tự hào', emoji: '🥰', color: '#FBCFE8' },
    { label: 'Bình yên', emoji: '😌', color: '#BBF7D0' },
  ]

  return (
    <View style={styles.container}>
      <Text style={styles.title}>🌱 Hôm nay con thấy thế nào?</Text>
      <Text style={styles.sub}>Bé hãy chọn cảm xúc của mình sau buổi vẽ và làm thủ công</Text>
      <View style={styles.grid}>
        {feelings.map((f) => (
          <Pressable
            key={f.label}
            style={[styles.card, selected === f.label && styles.cardActive]}
            onPress={() => setSelected(f.label)}
          >
            <Text style={styles.emoji}>{f.emoji}</Text>
            <Text style={styles.label}>{f.label}</Text>
          </Pressable>
        ))}
      </View>
      <Pressable style={styles.submitBtn} onPress={() => onSubmit(selected)}>
        <Text style={styles.submitBtnText}>Gửi cảm nhận cho cô/thầy ✓</Text>
      </Pressable>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFFBEB', padding: 28, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 26, fontWeight: 'bold', color: '#78350F', marginBottom: 8 },
  sub: { fontSize: 15, color: '#92400E', marginBottom: 28 },
  grid: { flexDirection: 'row', gap: 18, marginBottom: 32 },
  card: { width: 120, height: 130, backgroundColor: '#FFF', borderRadius: 24, justifyContent: 'center', alignItems: 'center', borderWidth: 2, borderColor: '#FDE68A' },
  cardActive: { borderColor: '#D97706', backgroundColor: '#FEF3C7', transform: [{ scale: 1.05 }] },
  emoji: { fontSize: 44, marginBottom: 8 },
  label: { fontSize: 15, fontWeight: 'bold', color: '#451A03' },
  submitBtn: { backgroundColor: '#D97706', paddingVertical: 16, paddingHorizontal: 36, borderRadius: 22 },
  submitBtnText: { color: '#FFF', fontSize: 17, fontWeight: 'bold' },
})
