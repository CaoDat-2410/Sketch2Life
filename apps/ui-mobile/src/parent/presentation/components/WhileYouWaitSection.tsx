import React, { useEffect, useMemo, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { waitChecklist } from '../../application/videoWait';
import { loadTicks, saveTicks } from '../../infrastructure/device/videoWaitStorage';
import { Card, SectionTitle, palette } from './ui';

type Props = {
  runId: string;
  activity: { title?: string | null; instructions_text?: string | null } | null;
};

/**
 * "Trong lúc chờ": a short outdoor checklist from the adult's own activity. The ticks stay on this device.
 * Nothing here talks to the server, so the screen costs no request while the video is made.
 */
export function WhileYouWaitSection({ runId, activity }: Props): React.JSX.Element {
  const items = useMemo(() => waitChecklist(activity), [activity]);
  const [ticked, setTicked] = useState<string[]>([]);

  useEffect(() => {
    let alive = true;
    void loadTicks(runId).then((ticks) => {
      if (alive) setTicked(ticks);
    });
    return () => {
      alive = false;
    };
  }, [runId]);

  function toggle(id: string): void {
    const next = ticked.includes(id) ? ticked.filter((item) => item !== id) : [...ticked, id];
    setTicked(next);
    void saveTicks(runId, next);
  }

  const done = items.filter((item) => ticked.includes(item.id)).length;
  return (
    <Card variant="creative" style={styles.card}>
      <SectionTitle variant="creative">Trong lúc chờ</SectionTitle>
      <Text style={styles.hint}>Cùng bé thử vài việc nhỏ ngoài trời ({done}/{items.length}).</Text>
      {items.map((item) => {
        const checked = ticked.includes(item.id);
        return (
          <TouchableOpacity
            key={item.id}
            accessibilityRole="checkbox"
            accessibilityState={{ checked }}
            onPress={() => toggle(item.id)}
            style={[styles.row, checked ? styles.rowChecked : null]}
          >
            <Text style={styles.box}>{checked ? '✓' : '○'}</Text>
            <Text style={[styles.label, checked ? styles.labelChecked : null]}>{item.label}</Text>
          </TouchableOpacity>
        );
      })}
    </Card>
  );
}

const styles = StyleSheet.create({
  card: { gap: 9, minWidth: 0 },
  hint: { color: palette.creativeMuted, fontSize: 12, lineHeight: 17 },
  row: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, minHeight: 44, paddingVertical: 8, paddingHorizontal: 10, borderRadius: 14, borderWidth: 1.2, borderColor: palette.creativeBorder, backgroundColor: palette.white },
  rowChecked: { backgroundColor: palette.creativeLavender },
  box: { color: palette.creativePrimary, fontSize: 16, lineHeight: 20, fontWeight: '800', width: 18 },
  label: { flex: 1, color: palette.creativeInk, fontSize: 13, lineHeight: 19, minWidth: 0 },
  labelChecked: { color: palette.creativeMuted, textDecorationLine: 'line-through' },
});
