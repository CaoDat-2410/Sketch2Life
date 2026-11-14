import React, { useState } from 'react';
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
        return <ParentBottomBarItem key={tab.id} tab={tab} active={active} onNavigate={onNavigate} />;
      })}
    </View>
  );
}

function ParentBottomBarItem({
  tab,
  active,
  onNavigate,
}: {
  tab: (typeof tabs)[number];
  active: boolean;
  onNavigate: Props['onNavigate'];
}): React.JSX.Element {
  const [focused, setFocused] = useState(false);

  return (
    <Pressable
      accessibilityRole="tab"
      accessibilityLabel={tab.label}
      accessibilityState={{ selected: active }}
      onPress={() => onNavigate(tab.id)}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={({ pressed }) => [styles.item, focused && styles.focusRing, pressed && styles.pressed]}
    >
      <Ionicons name={tab.icon} size={22} color={active ? palette.blue : palette.muted} accessible={false} />
      <Text style={[styles.label, active && styles.activeLabel]}>{tab.label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bar: {
    minHeight: 68,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingHorizontal: 12,
    paddingTop: 8,
    paddingBottom: 8,
    backgroundColor: palette.white,
    borderTopWidth: 1.5,
    borderTopColor: palette.outline,
    shadowColor: palette.ink,
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.07,
    shadowRadius: 8,
    elevation: 3,
  },
  item: { flex: 1, minHeight: 52, alignItems: 'center', justifyContent: 'center', gap: 3, borderRadius: 12, borderWidth: 3, borderColor: 'transparent' },
  focusRing: { borderColor: palette.focus },
  pressed: { backgroundColor: palette.paleBlue },
  label: { color: palette.muted, fontSize: 11, fontWeight: '600', textAlign: 'center' },
  activeLabel: { color: palette.blue, fontWeight: '800' },
});
