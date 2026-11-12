import {Pressable, StyleSheet, Text, View} from 'react-native';

import type {ParentRoute} from '../../app/navigation/parentRoutes';
import {ParentIcon, type ParentIconName} from './ParentCard';
import {sketchColors} from './SketchTokens';

const items: readonly Readonly<{route: ParentRoute; label: string; icon: ParentIconName}>[] = [
  {route: 'home', label: 'Trang chủ', icon: 'home'},
  {route: 'history', label: 'Lịch sử', icon: 'history'},
  {route: 'notifications', label: 'Thông báo', icon: 'notifications'},
  {route: 'settings', label: 'Cài đặt', icon: 'settings'},
];

export function ParentBottomNavigation({
  activeRoute,
  onNavigate,
}: Readonly<{activeRoute: ParentRoute; onNavigate: (route: ParentRoute) => void}>): React.JSX.Element {
  return (
    <View accessibilityRole="tabbar" style={styles.bar}>
      {items.map((item) => {
        const selected = item.route === activeRoute;
        return (
          <Pressable
            key={item.route}
            accessibilityRole="tab"
            accessibilityState={{selected}}
            accessibilityLabel={item.label}
            onPress={() => onNavigate(item.route)}
            style={({pressed}) => [styles.tab, pressed ? styles.pressed : undefined]}>
            <View style={[styles.iconWrap, selected ? styles.iconSelected : undefined]}>
              <ParentIcon name={item.icon} color={selected ? sketchColors.greenDark : sketchColors.muted} size={20} />
            </View>
            <Text style={[styles.label, selected ? styles.labelSelected : undefined]}>{item.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    minHeight: 68,
    paddingHorizontal: 8,
    paddingBottom: 4,
    borderTopWidth: 1,
    borderColor: sketchColors.line,
    backgroundColor: sketchColors.surface,
  },
  tab: {flex: 1, minHeight: 58, alignItems: 'center', justifyContent: 'center', gap: 3, borderRadius: 15},
  pressed: {opacity: 0.72},
  iconWrap: {width: 36, height: 30, alignItems: 'center', justifyContent: 'center', borderRadius: 12},
  iconSelected: {backgroundColor: sketchColors.greenSoft},
  label: {color: sketchColors.muted, fontSize: 9, fontWeight: '600'},
  labelSelected: {color: sketchColors.greenDark, fontWeight: '900'},
});
