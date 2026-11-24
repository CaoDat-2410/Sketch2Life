import React from 'react';
import { StyleSheet, Switch, Text, TextInput, TouchableOpacity, View } from 'react-native';
import type { ParentSubjectRoleV1 } from '../../domain/types';
import { palette } from '../components/ui';

type Props = {
  role: ParentSubjectRoleV1;
  onRename: (label: string) => void;
  onToggle: () => void;
  onMakeMain: () => void;
};

/** One non-main object of the drawing: editable name, "use in story" switch, promote button. */
export function SecondarySubjectRow({ role, onRename, onToggle, onMakeMain }: Props): React.JSX.Element {
  const used = role.role === 'secondary';
  return (
    <View style={[styles.row, !used && styles.rowOff]}>
      <TextInput
        accessibilityLabel={`Tên vật: ${role.label}`}
        value={role.label}
        onChangeText={onRename}
        maxLength={100}
        placeholder="Tên vật"
        placeholderTextColor={palette.creativeMuted}
        style={styles.input}
      />
      <View style={styles.controls}>
        <View style={styles.switchWrap}>
          <Switch
            accessibilityLabel={`Dùng ${role.label} trong truyện`}
            value={used}
            onValueChange={onToggle}
            trackColor={{ false: '#D9D2E3', true: palette.creativePrimary }}
          />
          <Text style={styles.switchLabel}>Dùng trong truyện</Text>
        </View>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={`Đặt ${role.label} làm chủ thể chính`}
          onPress={onMakeMain}
          style={styles.promote}
        >
          <Text style={styles.promoteLabel}>Đặt làm chủ thể chính</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { gap: 8, padding: 12, borderRadius: 16, backgroundColor: '#F8F3FF' },
  rowOff: { opacity: 0.7 },
  input: {
    minHeight: 46, borderRadius: 13, borderWidth: 1.2, borderColor: palette.creativeBorder,
    backgroundColor: '#fff', paddingHorizontal: 12, color: palette.creativeInk, fontSize: 14,
  },
  controls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' },
  switchWrap: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  switchLabel: { color: palette.creativeMuted, fontSize: 12, fontWeight: '700' },
  promote: { minHeight: 44, borderRadius: 13, paddingHorizontal: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: '#EFE6FB' },
  promoteLabel: { color: palette.creativePrimary, fontSize: 12, fontWeight: '800' },
});
