import React, { useState } from 'react'
import { View, Text, StyleSheet, Pressable } from 'react-native'

export function AdvancedDrawScreen({ onBack: _onBack, onComplete: _onComplete }: { onBack: () => void; onComplete: () => void }) {
  const [brushSize, setBrushSize] = useState(6)
  const sizes = [3, 6, 12, 20]

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>🍃 Bàn vẽ nâng cao - Bé Lá</Text>
        <View style={styles.sizeGroup}>
          <Text style={styles.sizeLabel}>Cỡ nét: </Text>
          {sizes.map((s) => (
            <Pressable
              key={s}
              style={[styles.sizeBtn, brushSize === s && styles.sizeActive]}
              onPress={() => setBrushSize(s)}
            >
              <Text style={styles.sizeText}>{s}px</Text>
            </Pressable>
          ))}
        </View>
      </View>
      <View style={styles.canvasContainer}>
        <Text style={styles.canvasNote}>Hỗ trợ vẽ nhiều lớp chi tiết cho thực vật, gân lá và hoa cúc</Text>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0FDF4', padding: 16 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#166534' },
  sizeGroup: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sizeLabel: { fontSize: 14, fontWeight: '600', color: '#374151' },
  sizeBtn: { paddingVertical: 6, paddingHorizontal: 12, borderRadius: 12, backgroundColor: '#DCFCE7' },
  sizeActive: { backgroundColor: '#16A34A' },
  sizeText: { fontSize: 13, fontWeight: 'bold', color: '#0F172A' },
  canvasContainer: { flex: 1, backgroundColor: '#FFF', borderRadius: 24, borderWidth: 2, borderColor: '#BBF7D0', justifyContent: 'center', alignItems: 'center' },
  canvasNote: { color: '#86EFAC', fontSize: 16, fontWeight: '600' },
})
