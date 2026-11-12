import React from 'react'
import { Text, StyleSheet, TextStyle } from 'react-native'

export function Heading({ children, style }: { children: React.ReactNode; style?: TextStyle }) {
  return <Text style={[styles.heading, style]}>{children}</Text>
}

const styles = StyleSheet.create({
  heading: { fontSize: 22, fontWeight: '700', color: '#0F172A' },
})
