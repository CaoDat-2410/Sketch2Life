import React, { useState } from 'react'
import { View, Text, TextInput, StyleSheet, Image, Pressable, Alert } from 'react-native'

export interface JoinScreenProps {
  onJoin: (code: string, kid: 'Mây' | 'Lá') => void
  onHelp?: () => void
}

export function JoinScreen({ onJoin, onHelp }: JoinScreenProps) {
  const [digits, setDigits] = useState(['', '', '', ''])
  const [selectedKid, setSelectedKid] = useState<'Mây' | 'Lá'>('Mây')

  const handleDigitChange = (val: string, index: number) => {
    const clean = val.replace(/[^0-9]/g, '')
    const next = [...digits]
    next[index] = clean.slice(-1)
    setDigits(next)
  }

  const handleJoin = () => {
    const fullCode = digits.join('')
    if (fullCode.length < 4) {
      Alert.alert('Chưa nhập đủ mã', 'Bé ơi hãy nhờ cô/thầy nhập đủ 4 số phòng nhé!')
      return
    }
    onJoin(fullCode, selectedKid)
  }

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>🌱 Bé tham gia buổi học</Text>
        <Text style={styles.subtitle}>Nhập mã 4 số cô/thầy cung cấp để vào lớp vẽ</Text>
        <View style={styles.codeRow}>
          {digits.map((d, i) => (
            <TextInput
              key={i}
              style={styles.codeBox}
              value={d}
              onChangeText={(v) => handleDigitChange(v, i)}
              keyboardType="number-pad"
              maxLength={1}
            />
          ))}
        </View>
        <Text style={styles.label}>Bé chọn bạn đồng hành hôm nay:</Text>
        <View style={styles.kidRow}>
          <Pressable
            style={[styles.kidChoice, selectedKid === 'Mây' && styles.kidActive]}
            onPress={() => setSelectedKid('Mây')}
          >
            <Text style={styles.kidText}>☁️ Bạn Mây</Text>
          </Pressable>
          <Pressable
            style={[styles.kidChoice, selectedKid === 'Lá' && styles.kidActive]}
            onPress={() => setSelectedKid('Lá')}
          >
            <Text style={styles.kidText}>🍃 Bạn Lá</Text>
          </Pressable>
        </View>
        <Pressable style={styles.joinBtn} onPress={handleJoin}>
          <Text style={styles.joinBtnText}>Vào lớp ngay ➜</Text>
        </Pressable>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F0F9FF' },
  card: { width: 500, padding: 32, borderRadius: 28, backgroundColor: '#FFFFFF', shadowColor: '#000', shadowOpacity: 0.08, shadowRadius: 16 },
  title: { fontSize: 24, fontWeight: '700', color: '#0F172A', textAlign: 'center', marginBottom: 8 },
  subtitle: { fontSize: 14, color: '#64748B', textAlign: 'center', marginBottom: 20 },
  codeRow: { flexDirection: 'row', justifyContent: 'center', gap: 12, marginBottom: 24 },
  codeBox: { width: 56, height: 64, borderWidth: 2, borderColor: '#CBD5E1', borderRadius: 16, textAlign: 'center', fontSize: 28, fontWeight: 'bold', color: '#0F172A' },
  label: { fontSize: 15, fontWeight: '600', color: '#334155', marginBottom: 8, textAlign: 'center' },
  kidRow: { flexDirection: 'row', justifyContent: 'center', gap: 16, marginBottom: 24 },
  kidChoice: { paddingVertical: 12, paddingHorizontal: 20, borderRadius: 20, borderWidth: 2, borderColor: '#E2E8F0', backgroundColor: '#F8FAFC' },
  kidActive: { borderColor: '#1685F8', backgroundColor: '#EFF6FF' },
  kidText: { fontSize: 16, fontWeight: '600', color: '#1E293B' },
  joinBtn: { backgroundColor: '#1685F8', borderRadius: 20, paddingVertical: 16, alignItems: 'center' },
  joinBtnText: { color: '#FFF', fontSize: 18, fontWeight: 'bold' },
})
