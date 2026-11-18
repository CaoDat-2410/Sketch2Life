import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
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
  { id: 'lessons', label: 'Khám phá', icon: 'compass-outline' },
  { id: 'activity', label: 'Câu chuyện', icon: 'book-outline' },
  { id: 'profiles', label: 'Cá nhân', icon: 'person-circle-outline' },
];

export function ParentBottomBar({ activeTab, onNavigate, onStart, startLabel }: Props): React.JSX.Element {
  const [startFocused, setStartFocused] = useState(false);
  const { bottom, left, right } = useSafeAreaInsets();
  const totalBarHeight = 56 + bottom;

  return (
    <View style={[styles.bar, { height: totalBarHeight, flexBasis: totalBarHeight, paddingLeft: left, paddingRight: right }]}>
      <View style={styles.tabList} accessibilityRole="tablist">
        {tabs.slice(0, 2).map((tab) => (
          <ParentBottomBarItem key={tab.id} tab={tab} active={activeTab === tab.id} onNavigate={onNavigate} />
        ))}
        <View style={styles.centerSlot} accessible={false}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={startLabel === 'Tiếp tục' ? 'Tiếp tục buổi sáng tạo đang mở' : 'Mở luồng sáng tạo'}
            onPress={onStart}
            onFocus={() => setStartFocused(true)}
            onBlur={() => setStartFocused(false)}
            style={({ pressed }) => [styles.startAction, startFocused && styles.startActionFocused, pressed && styles.startActionPressed]}
          >
            <View style={styles.startButtonRing}>
              <LinearGradient colors={['#9838F3', '#6818D2']} start={{ x: 0.3, y: 0 }} end={{ x: 0.8, y: 1 }} style={styles.startButton}>
                <Ionicons name={startLabel === 'Tiếp tục' ? 'play' : 'camera-outline'} size={25} color="#FFFFFF" accessible={false} />
              </LinearGradient>
            </View>
            <Text style={styles.startLabel}>Sáng tạo</Text>
          </Pressable>
        </View>
        {tabs.slice(2).map((tab) => (
          <ParentBottomBarItem key={tab.id} tab={tab} active={activeTab === tab.id} onNavigate={onNavigate} />
        ))}
      </View>
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
      style={({ pressed }) => [styles.item, active && styles.activeItem, focused && styles.focusRing, pressed && styles.pressed]}
    >
      <View style={styles.iconBadge}>
        <Ionicons name={active && tab.id === 'home' ? 'home' : tab.icon} size={27} color={active ? '#7435D5' : '#756A80'} accessible={false} />
      </View>
      <Text style={[styles.label, active && styles.activeLabel]}>{tab.label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bar: {
    position: 'relative',
    height: 56,
    flexBasis: 56,
    backgroundColor: '#FFFEFD',
    borderTopLeftRadius: 26,
    borderTopRightRadius: 26,
    borderTopWidth: 1,
    borderTopColor: '#F0E7F5',
    shadowColor: '#512A78',
    shadowOffset: { width: 0, height: -5 },
    shadowOpacity: 0.12,
    shadowRadius: 18,
    elevation: 9,
  },
  tabList: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 6,
    paddingTop: 3,
    paddingBottom: 3,
  },
  item: { flex: 1, minWidth: 0, minHeight: 48, alignItems: 'center', justifyContent: 'center', gap: 1, borderRadius: 18, borderWidth: 2, borderColor: 'transparent' },
  activeItem: { backgroundColor: '#F1E7FF' },
  centerSlot: { position: 'relative', flex: 1, minWidth: 0, minHeight: 48, alignItems: 'center', justifyContent: 'center', overflow: 'visible' },
  iconBadge: { width: 34, height: 29, alignItems: 'center', justifyContent: 'center' },
  focusRing: { borderColor: palette.focus, borderWidth: 3 },
  pressed: { backgroundColor: '#E9D9FF' },
  startAction: { position: 'absolute', zIndex: 4, top: -5, left: 0, right: 0, minHeight: 68, alignItems: 'center', justifyContent: 'flex-start', borderRadius: 20, borderWidth: 2, borderColor: 'transparent' },
  startActionFocused: { borderColor: palette.focus, borderWidth: 3 },
  startActionPressed: { opacity: 0.82 },
  startButtonRing: { width: 52, height: 52, borderRadius: 26, borderWidth: 4, borderColor: '#FFFFFF', backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center', elevation: 5, shadowColor: '#5A258C', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.16, shadowRadius: 7 },
  startButton: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  startLabel: { marginTop: 1, color: '#5A1D9E', fontSize: 11, lineHeight: 14, fontWeight: '800', textAlign: 'center' },
  label: { color: '#6E6379', fontSize: 10.5, lineHeight: 13, fontWeight: '700', textAlign: 'center', flexShrink: 1 },
  activeLabel: { color: '#7435D5', fontWeight: '900' },
});
