import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { palette } from '../components/ui';

export type ParentMainTab = 'home' | 'lessons' | 'activity' | 'profiles';

type Props = {
  activeTab: ParentMainTab;
  onNavigate: (tab: ParentMainTab) => void;
  onStart: () => void;
  startLabel: 'Bắt đầu' | 'Tiếp tục';
};

const tabs: { id: ParentMainTab; label: string; icon: React.ComponentProps<typeof Ionicons>['name'] }[] = [
  { id: 'home', label: 'Trang chủ', icon: 'home-outline' },
  { id: 'lessons', label: 'Bài giảng', icon: 'book-outline' },
  { id: 'activity', label: 'Hoạt động', icon: 'time-outline' },
  { id: 'profiles', label: 'Gia đình', icon: 'people-outline' },
];

export function ParentBottomBar({ activeTab, onNavigate, onStart, startLabel }: Props): React.JSX.Element {
  const [startFocused, setStartFocused] = useState(false);

  return (
    <View style={styles.bar}>
      <View style={styles.tabList} accessibilityRole="tablist">
        {tabs.slice(0, 2).map((tab) => (
          <ParentBottomBarItem key={tab.id} tab={tab} active={activeTab === tab.id} onNavigate={onNavigate} />
        ))}
        <View style={styles.centerSlot} accessible={false} />
        {tabs.slice(2).map((tab) => (
          <ParentBottomBarItem key={tab.id} tab={tab} active={activeTab === tab.id} onNavigate={onNavigate} />
        ))}
      </View>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={startLabel === 'Tiếp tục' ? 'Tiếp tục buổi đang mở' : 'Bắt đầu buổi học'}
        onPress={onStart}
        onFocus={() => setStartFocused(true)}
        onBlur={() => setStartFocused(false)}
        style={({ pressed }) => [styles.startAction, startFocused && styles.startActionFocused, pressed && styles.startActionPressed]}
      >
        <View style={styles.startButton}>
          <Ionicons name={startLabel === 'Tiếp tục' ? 'play' : 'add'} size={24} color={palette.background} accessible={false} />
        </View>
        <Text style={styles.startLabel}>{startLabel}</Text>
      </Pressable>
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
      <View style={[styles.iconBadge, active && styles.activeIconBadge]}>
        <Ionicons name={tab.icon} size={19} color={active ? palette.ink : palette.muted} accessible={false} />
      </View>
      <Text style={[styles.label, active && styles.activeLabel]}>{tab.label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bar: {
    position: 'relative',
    height: 62,
    flexBasis: 62,
    backgroundColor: palette.background,
    borderTopWidth: 1,
    borderTopColor: palette.outline,
    shadowColor: palette.ink,
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.07,
    shadowRadius: 8,
    elevation: 3,
  },
  tabList: {
    height: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingHorizontal: 7,
    paddingTop: 4,
    paddingBottom: 4,
  },
  item: { flex: 1, minWidth: 0, minHeight: 52, alignItems: 'center', justifyContent: 'center', gap: 1, borderRadius: 12, borderWidth: 2, borderColor: 'transparent' },
  centerSlot: { flex: 1, minWidth: 0, minHeight: 52 },
  iconBadge: { width: 25, height: 25, alignItems: 'center', justifyContent: 'center', borderRadius: 999, borderWidth: 2, borderColor: 'transparent', backgroundColor: 'transparent' },
  activeIconBadge: { borderColor: palette.outline, backgroundColor: palette.butter },
  focusRing: { borderColor: palette.focus, borderWidth: 3 },
  pressed: { backgroundColor: palette.paleBlue },
  startAction: { position: 'absolute', zIndex: 4, top: -16, left: '50%', width: 70, minHeight: 62, marginLeft: -35, alignItems: 'center', justifyContent: 'flex-start', borderRadius: 16, borderWidth: 2, borderColor: 'transparent' },
  startActionFocused: { borderColor: palette.focus, borderWidth: 3 },
  startActionPressed: { opacity: 0.82 },
  startButton: { width: 52, height: 52, borderRadius: 26, alignItems: 'center', justifyContent: 'center', borderWidth: 3, borderColor: palette.background, backgroundColor: palette.ink, elevation: 5, shadowColor: palette.ink, shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.24, shadowRadius: 5 },
  startLabel: { color: palette.ink, fontSize: 8, lineHeight: 10, fontWeight: '800', textAlign: 'center' },
  label: { color: palette.muted, fontSize: 9, lineHeight: 12, fontWeight: '600', textAlign: 'center', flexShrink: 1 },
  activeLabel: { color: palette.ink, fontWeight: '800' },
});
