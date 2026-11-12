import {StyleSheet, Text, View} from 'react-native';

import {ParentButton, ParentCard, ParentIcon, type ParentIconName} from './ParentCard';
import {sketchColors, sketchSpace} from './SketchTokens';

export function PreviewBanner({
  title = 'Bản trải nghiệm',
  body = 'Dữ liệu và thao tác trong màn này chưa đồng bộ với máy chủ.',
}: Readonly<{title?: string; body?: string}>): React.JSX.Element {
  return (
    <View accessibilityRole="summary" style={styles.previewBanner}>
      <View style={styles.previewIcon}><ParentIcon name="spark" size={17} color={sketchColors.greenDark} /></View>
      <View style={styles.previewCopy}>
        <Text style={styles.previewTitle}>{title}</Text>
        <Text style={styles.previewBody}>{body}</Text>
      </View>
    </View>
  );
}

export function InfoBanner({
  title,
  body,
  tone = 'info',
}: Readonly<{title: string; body: string; tone?: 'info' | 'warning' | 'error'}>): React.JSX.Element {
  const backgroundColor = tone === 'error' ? sketchColors.coralSoft : tone === 'warning' ? sketchColors.goldSoft : sketchColors.blueSoft;
  const color = tone === 'error' ? '#8E4438' : tone === 'warning' ? '#715814' : '#426C87';
  return (
    <View accessibilityRole="alert" style={[styles.infoBanner, {backgroundColor}]}>
      <Text style={[styles.infoTitle, {color}]}>{title}</Text>
      <Text style={[styles.infoBody, {color}]}>{body}</Text>
    </View>
  );
}

export function EmptyState({
  icon = 'book',
  title,
  description,
  action,
  onAction,
}: Readonly<{
  icon?: ParentIconName;
  title: string;
  description: string;
  action?: string;
  onAction?: () => void;
}>): React.JSX.Element {
  return (
    <ParentCard style={styles.emptyState}>
      <View style={styles.emptyIcon}><ParentIcon name={icon} size={25} /></View>
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.emptyDescription}>{description}</Text>
      {action && onAction ? <ParentButton title={action} onPress={onAction} variant="secondary" /> : null}
    </ParentCard>
  );
}

const styles = StyleSheet.create({
  previewBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: '#D7E7D8',
    borderRadius: 14,
    backgroundColor: '#EEF6EC',
  },
  previewIcon: {width: 29, height: 29, alignItems: 'center', justifyContent: 'center', borderRadius: 10, backgroundColor: '#D9EBD9'},
  previewCopy: {flex: 1, gap: 3},
  previewTitle: {color: sketchColors.greenDark, fontSize: 11, fontWeight: '800'},
  previewBody: {color: sketchColors.inkSoft, fontSize: 11, lineHeight: 16},
  infoBanner: {padding: 13, borderRadius: 14, gap: 4},
  infoTitle: {fontSize: 12, fontWeight: '800'},
  infoBody: {fontSize: 11, lineHeight: 16},
  emptyState: {alignItems: 'center', gap: sketchSpace.md, paddingVertical: 25},
  emptyIcon: {width: 52, height: 52, alignItems: 'center', justifyContent: 'center', borderRadius: 17, backgroundColor: sketchColors.greenSoft},
  emptyTitle: {color: sketchColors.ink, fontSize: 16, fontWeight: '800', textAlign: 'center'},
  emptyDescription: {color: sketchColors.muted, fontSize: 12, lineHeight: 18, textAlign: 'center'},
});
