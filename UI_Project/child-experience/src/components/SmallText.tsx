import React from 'react'
import { Text, StyleSheet, TextStyle } from 'react-native'

export function SmallText({ children, style }: { children: React.ReactNode; style?: TextStyle }) {
  return <Text style={[styles.small, style]}>{children}</Text>
}

const styles = StyleSheet.create({
  small: { fontSize: 13, color: '#64748B', lineHeight: 18 },
})
