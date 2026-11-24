import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { palette } from './ui';

type Props = {
  title: string;
  description: string;
  note: string;
  statusLabel?: string;
  testID: string;
  prominent?: boolean;
  mode?: 'processing' | 'reconciliation';
  showElapsed?: boolean;
};

export function ParentAiLoadingState({
  title,
  description,
  note,
  statusLabel = 'Đang xử lý',
  testID,
  prominent = false,
  mode = 'processing',
  showElapsed = true,
}: Props): React.JSX.Element {
  const reconciliationRequired = mode === 'reconciliation';
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    const startedAt = Date.now();
    const timer = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <View
      testID={testID}
      accessibilityRole={reconciliationRequired ? 'alert' : 'progressbar'}
      accessibilityState={{ busy: !reconciliationRequired }}
      accessibilityLabel={`${title}. ${description}`}
      accessibilityLiveRegion="polite"
      style={[styles.panel, prominent && styles.panelProminent, reconciliationRequired && styles.panelReconciliation]}
    >
      <View style={styles.mainRow}>
        <View style={[styles.spinnerTile, prominent && styles.spinnerTileProminent, reconciliationRequired && styles.reconciliationTile]}>
          {reconciliationRequired
            ? <Ionicons name="cloud-offline-outline" size={28} color="#8A6200" accessible={false} />
            : <ActivityIndicator size="large" color={palette.creativePrimary} accessible={false} />}
        </View>
        <View style={styles.copy}>
          <Text accessibilityRole="header" style={[styles.title, prominent && styles.prominentText]}>{title}</Text>
          <Text style={[styles.description, prominent && styles.prominentText]}>{description}</Text>
        </View>
      </View>
      <View style={styles.footer}>
        <View style={styles.waitLabel}>
          <Ionicons
            name={reconciliationRequired ? 'alert-circle-outline' : 'time-outline'}
            size={16}
            color={reconciliationRequired ? '#8A6200' : palette.creativePrimary}
            accessible={false}
          />
          <Text style={styles.waitText}>{statusLabel}</Text>
        </View>
        {showElapsed && !reconciliationRequired ? (
          <Text accessibilityLabel={`Đã chờ ${formatElapsedTime(elapsedSeconds)}`} style={styles.elapsed}>
            {formatElapsedTime(elapsedSeconds)}
          </Text>
        ) : null}
      </View>
      <Text style={[styles.note, prominent && styles.prominentText]}>{note}</Text>
    </View>
  );
}

export function formatElapsedTime(totalSeconds: number): string {
  const safeSeconds = Number.isFinite(totalSeconds) ? Math.max(0, Math.floor(totalSeconds)) : 0;
  const minutes = Math.floor(safeSeconds / 60);
  const seconds = safeSeconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

const styles = StyleSheet.create({
  panel: {
    gap: 13,
    padding: 16,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: palette.creativePrimary,
    backgroundColor: '#F4ECFF',
    elevation: 3,
  },
  panelProminent: {
    borderWidth: 3,
    borderColor: '#5522A8',
    backgroundColor: palette.creativePrimary,
    elevation: 7,
  },
  panelReconciliation: { borderColor: '#D7A51A', backgroundColor: '#FFF7D6', elevation: 2 },
  mainRow: { flexDirection: 'row', alignItems: 'center', gap: 13 },
  spinnerTile: {
    width: 58,
    height: 58,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#E7D5FF',
  },
  spinnerTileProminent: { backgroundColor: '#FFFFFF' },
  reconciliationTile: { backgroundColor: '#FFE9A8' },
  copy: { flex: 1, minWidth: 0, gap: 5 },
  title: { color: palette.creativeInk, fontSize: 16, lineHeight: 21, fontWeight: '800' },
  description: { color: palette.creativeInk, fontSize: 13, lineHeight: 19 },
  footer: {
    minHeight: 39,
    paddingHorizontal: 11,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFEFF',
    borderWidth: 1,
    borderColor: palette.creativeBorder,
  },
  waitLabel: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  waitText: { color: palette.creativeInk, fontSize: 12, fontWeight: '700' },
  elapsed: { color: palette.creativePrimary, fontSize: 16, fontWeight: '800', fontVariant: ['tabular-nums'] },
  note: { color: palette.creativeMuted, fontSize: 12, lineHeight: 17 },
  prominentText: { color: '#FFFFFF' },
});
