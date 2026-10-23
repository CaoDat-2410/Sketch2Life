import React from 'react'
import { View, Text, StyleSheet, Pressable, Image } from 'react-native'

export interface LobbyScreenProps {
  kidName: string
  onReady: () => void
  onHelp?: () => void
}

export function LobbyScreen({ kidName, onReady, onHelp }: LobbyScreenProps) {
  return (
    <View style={styles.container}>
      <View style={styles.bubble}>
        <Text style={styles.heading}>Chào mừng bạn {kidName}! 🌱</Text>
        <Text style={styles.text}>Hãy đợi cô/thầy giáo và các bạn cùng vào phòng nhé. Chúng mình chuẩn bị vẽ khu vườn kỳ diệu!</Text>
        <View style={styles.avatarList}>
          <View style={styles.avatarItem}><Text style={styles.avatarIcon}>☁️</Text><Text style={styles.avatarName}>Mây (Sẵn sàng)</Text></View>
          <View style={styles.avatarItem}><Text style={styles.avatarIcon}>🍃</Text><Text style={styles.avatarName}>Lá (Sẵn sàng)</Text></View>
          <View style={styles.avatarItem}><Text style={styles.avatarIcon}>☀️</Text><Text style={styles.avatarName}>Nắng (Đang vào)</Text></View>
        </View>
        <Pressable style={styles.readyBtn} onPress={onReady}>
          <Text style={styles.readyBtnText}>Con đã sẵn sàng ✓</Text>
        </Pressable>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#EFF6FF', justifyContent: 'center', alignItems: 'center' },
  bubble: { width: 560, backgroundColor: '#FFF', borderRadius: 32, padding: 32, alignItems: 'center', shadowOpacity: 0.1, shadowRadius: 20 },
  heading: { fontSize: 26, fontWeight: 'bold', color: '#1E3A8A', marginBottom: 12 },
  text: { fontSize: 16, color: '#475569', textAlign: 'center', lineHeight: 24, marginBottom: 24 },
  avatarList: { flexDirection: 'row', gap: 20, marginBottom: 28 },
  avatarItem: { alignItems: 'center', padding: 12, backgroundColor: '#F1F5F9', borderRadius: 18 },
  avatarIcon: { fontSize: 32, marginBottom: 4 },
  avatarName: { fontSize: 13, fontWeight: '600', color: '#334155' },
  readyBtn: { backgroundColor: '#31C978', paddingVertical: 16, paddingHorizontal: 36, borderRadius: 24 },
  readyBtnText: { color: '#FFF', fontSize: 18, fontWeight: 'bold' },
})
