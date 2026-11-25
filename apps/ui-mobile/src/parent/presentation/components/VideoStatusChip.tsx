import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { palette } from './ui';

type Props = { text: string; badge: boolean; onPress: () => void };

/** Floating status of the video that is being made (or just finished); tapping it opens the video step. */
export function VideoStatusChip({ text, badge, onPress }: Props): React.JSX.Element {
  return (
    <View pointerEvents="box-none" style={styles.layer}>
      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel={`Trạng thái video: ${text}`}
        onPress={onPress}
        style={[styles.chip, badge ? styles.chipReady : null]}
      >
        <Text style={styles.text} numberOfLines={1}>{text}</Text>
        {badge ? <View accessibilityLabel="Video mới" style={styles.badge} /> : null}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  layer: { position: 'absolute', left: 0, right: 0, bottom: 84, alignItems: 'center' },
  chip: { flexDirection: 'row', alignItems: 'center', gap: 8, maxWidth: '90%', minHeight: 40, paddingHorizontal: 16, borderRadius: 20, backgroundColor: palette.creativePrimary, elevation: 4 },
  chipReady: { backgroundColor: '#2E7D4F' },
  text: { color: palette.white, fontSize: 12, fontWeight: '800', flexShrink: 1 },
  badge: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#FFD54A' },
});
