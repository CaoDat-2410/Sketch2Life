import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { palette } from '../components/ui';

export type ParentMainTab = 'home' | 'lessons' | 'start' | 'profiles';

type Props = {
  activeTab: ParentMainTab;
  onNavigate: (tab: ParentMainTab) => void;
};

const tabs: { id: ParentMainTab; label: string; icon: React.ComponentProps<typeof Ionicons>['name'] }[] = [
  { id: 'home', label: 'Trang chủ', icon: 'home-outline' },
  { id: 'lessons', label: 'Bài giảng', icon: 'book-outline' },
  { id: 'start', label: 'Bắt đầu', icon: 'add-circle-outline' },
  { id: 'profiles', label: 'Hồ sơ', icon: 'people-outline' },
];

export function ParentBottomBar({ activeTab, onNavigate }: Props): React.JSX.Element {
  return (
    <View style={styles.bar} accessibilityRole="tablist">
      {tabs.map((tab) => {
        const active = activeTab === tab.id;
        return (
          <Pressable
            key={tab.id}
            accessibilityRole="tab"
            accessibilityLabel={tab.label}
            accessibilityState={{ selected: active }}
            onPress={() => onNavigate(tab.id)}
            style={styles.item}
          >
            <Ionicons name={tab.icon} size={22} color={active ? palette.blue : palette.muted} />
            <Text style={[styles.label, active && styles.activeLabel]}>{tab.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    minHeight: 66,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingHorizontal: 12,
    paddingTop: 6,
    paddingBottom: 6,
    backgroundColor: palette.white,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: palette.border,
  },
  item: { flex: 1, minHeight: 52, alignItems: 'center', justifyContent: 'center', gap: 3 },
  label: { color: palette.muted, fontSize: 11, fontWeight: '600' },
  activeLabel: { color: palette.blue, fontWeight: '800' },
});
