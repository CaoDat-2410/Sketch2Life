import React from 'react';
import { StyleSheet, Switch, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Card, ScreenFrame } from '../components/ui';

type Props = {
  sketchGuideEnabled: boolean;
  onSketchGuideEnabled: (enabled: boolean) => void;
  onBack: () => void;
};

export function SettingsScreen(props: Props): React.JSX.Element {
  return (
    <ScreenFrame title="Cài đặt" subtitle="Tùy chỉnh trải nghiệm trên thiết bị." onBack={props.onBack} visualTone="creative" safeAreaEdges={['top', 'right', 'left']}>
      <View style={styles.group}>
        <Text style={styles.groupTitle}>Trong buổi vẽ</Text>
        <Card style={styles.settingCard}>
          <View style={styles.preferenceRow}>
            <View style={[styles.rowIcon, styles.guideIcon]}><Ionicons name="color-wand-outline" size={19} color="#7435D5" accessible={false} /></View>
            <View style={styles.rowCopy}>
              <Text style={styles.rowTitle}>Gợi ý nét vẽ</Text>
            </View>
            <Switch
              value={props.sketchGuideEnabled}
              onValueChange={props.onSketchGuideEnabled}
              accessibilityLabel="Bật gợi ý nét vẽ trong phiên hiện tại"
              trackColor={{ false: '#D8D1DE', true: '#CBB0F3' }}
              thumbColor={props.sketchGuideEnabled ? '#7435D5' : '#FFFFFF'}
            />
          </View>
          <View style={styles.localOnlyNote}>
            <Ionicons name="information-circle-outline" size={17} color="#376388" accessible={false} />
            <Text style={styles.localOnlyText}>Chỉ áp dụng cho buổi hiện tại, chưa lưu vào tài khoản.</Text>
          </View>
        </Card>
      </View>

    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  group: { gap: 7 },
  groupTitle: { paddingHorizontal: 3, color: '#766781', fontSize: 12, lineHeight: 17, fontWeight: '800' },
  settingCard: { gap: 13, backgroundColor: '#FFFEFF', borderColor: '#E8DDF1', borderWidth: 1.2, borderRadius: 20 },
  preferenceRow: { minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 10 },
  rowIcon: { width: 38, height: 38, borderRadius: 13, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  guideIcon: { backgroundColor: '#F1E7FF' },
  rowCopy: { flex: 1, minWidth: 0, gap: 2 },
  rowTitle: { color: '#332342', fontSize: 13, lineHeight: 18, fontWeight: '800', flexShrink: 1 },
  localOnlyNote: { minHeight: 43, paddingHorizontal: 10, paddingVertical: 8, borderRadius: 13, flexDirection: 'row', alignItems: 'flex-start', gap: 7, backgroundColor: '#E7F2FC' },
  localOnlyText: { flex: 1, color: '#315D7C', fontSize: 11, lineHeight: 16 },
});
