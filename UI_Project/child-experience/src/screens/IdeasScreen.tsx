import React from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export function IdeasScreen({ onSelectIdea, onBack }: { onSelectIdea: (idea: string) => void; onBack: () => void }) {
  const ideas = [
    { title: 'Hoa khoe sắc', desc: 'Những cánh hoa tròn đón nắng ban mai', icon: '🌸' },
    { title: 'Chiếc lá xanh', desc: 'Có cuống lá và những đường gân uốn lượn', icon: '🍃' },
    { title: 'Mặt trời ấm áp', desc: 'Chiếu những tia nắng vàng rực rỡ', icon: '☀️' },
  ]

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>💡 Gợi ý hình vẽ thiên nhiên</Text>
      <Text style={styles.sub}>Bé có thể tham khảo hoặc vẽ sáng tạo theo cách của riêng mình</Text>
      <View style={styles.cardGrid}>
        {ideas.map((item, idx) => (
          <Pressable key={idx} style={styles.card} onPress={() => onSelectIdea(item.title)}>
            <Text style={styles.icon}>{item.icon}</Text>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.desc}>{item.desc}</Text>
          </Pressable>
        ))}
      </View>
      <Pressable style={styles.backBtn} onPress={onBack}>
        <Text style={styles.backBtnText}>Quay lại bàn vẽ ➜</Text>
      </Pressable>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFFBEB', padding: 28, alignItems: 'center' },
  heading: { fontSize: 24, fontWeight: 'bold', color: '#92400E', marginBottom: 6 },
  sub: { fontSize: 15, color: '#B45309', marginBottom: 24 },
  cardGrid: { flexDirection: 'row', gap: 20, marginBottom: 28 },
  card: { width: 220, padding: 24, backgroundColor: '#FFF', borderRadius: 24, alignItems: 'center', borderWidth: 2, borderColor: '#FDE68A' },
  icon: { fontSize: 44, marginBottom: 12 },
  title: { fontSize: 18, fontWeight: 'bold', color: '#78350F', marginBottom: 8 },
  desc: { fontSize: 13, color: '#92400E', textAlign: 'center', lineHeight: 18 },
  backBtn: { backgroundColor: '#F59E0B', paddingVertical: 14, paddingHorizontal: 32, borderRadius: 20 },
  backBtnText: { color: '#FFF', fontWeight: 'bold', fontSize: 16 },
})
