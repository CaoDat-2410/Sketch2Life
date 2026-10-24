import { useState } from 'react'
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native'

export interface JoinScreenProps {
  /** Parent supplies the BE1 room-code request handler; this component never admits a child itself. */
  onJoin: (roomCode: string) => void
  onHelp?: () => void
}

export function JoinScreen({ onJoin, onHelp }: JoinScreenProps) {
  const [digits, setDigits] = useState(Array<string>(6).fill(''))

  const handleDigitChange = (value: string, index: number) => {
    const incoming = value.replace(/\D/g, '')
    const next = [...digits]
    if (incoming.length > 1) {
      incoming.slice(0, 6 - index).split('').forEach((digit, offset) => {
        next[index + offset] = digit
      })
    } else {
      next[index] = incoming
    }
    setDigits(next)
  }

  const handleJoin = () => {
    const roomCode = digits.join('')
    if (!/^\d{6}$/.test(roomCode)) {
      Alert.alert('Chưa nhập đủ mã', 'Mã phòng gồm sáu chữ số. Hãy kiểm tra lại với cô/thầy nhé!')
      return
    }
    onJoin(roomCode)
  }

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>🌱 Bé tham gia buổi học</Text>
        <Text style={styles.subtitle}>Nhập mã phòng sáu số cô/thầy cung cấp</Text>
        <View style={styles.codeRow}>
          {digits.map((digit, index) => (
            <TextInput
              key={index}
              accessibilityLabel={`Số thứ ${index + 1} của mã phòng`}
              style={styles.codeBox}
              value={digit}
              onChangeText={(value) => handleDigitChange(value, index)}
              keyboardType="number-pad"
              maxLength={6}
            />
          ))}
        </View>
        <Pressable accessibilityRole="button" style={styles.joinBtn} onPress={handleJoin}>
          <Text style={styles.joinBtnText}>Gửi yêu cầu tham gia ➜</Text>
        </Pressable>
        {onHelp && (
          <Pressable accessibilityRole="button" style={styles.helpButton} onPress={onHelp}>
            <Text style={styles.helpText}>Nhờ cô/thầy giúp</Text>
          </Pressable>
        )}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F0F9FF' },
  card: { width: 500, padding: 32, borderRadius: 28, backgroundColor: '#FFFFFF', shadowColor: '#000', shadowOpacity: 0.08, shadowRadius: 16 },
  title: { fontSize: 24, fontWeight: '700', color: '#0F172A', textAlign: 'center', marginBottom: 8 },
  subtitle: { fontSize: 14, color: '#64748B', textAlign: 'center', marginBottom: 20 },
  codeRow: { flexDirection: 'row', justifyContent: 'center', gap: 8, marginBottom: 24 },
  codeBox: { width: 48, height: 64, borderWidth: 2, borderColor: '#CBD5E1', borderRadius: 16, textAlign: 'center', fontSize: 28, fontWeight: 'bold', color: '#0F172A' },
  joinBtn: { backgroundColor: '#1685F8', borderRadius: 20, paddingVertical: 16, alignItems: 'center' },
  joinBtnText: { color: '#FFF', fontSize: 18, fontWeight: 'bold' },
  helpButton: { alignItems: 'center', marginTop: 14 },
  helpText: { color: '#1685F8', fontSize: 15, fontWeight: '600' },
})
