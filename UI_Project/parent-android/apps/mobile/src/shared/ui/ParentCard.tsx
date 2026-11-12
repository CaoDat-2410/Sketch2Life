import type {ReactNode} from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
  type StyleProp,
  type TextInputProps,
  type ViewStyle,
} from 'react-native';

import {sketchColors, sketchRadius, sketchShadow, sketchSpace} from './SketchTokens';

export type ParentIconName =
  | 'back'
  | 'home'
  | 'history'
  | 'notifications'
  | 'settings'
  | 'child'
  | 'book'
  | 'camera'
  | 'voice'
  | 'spark'
  | 'check'
  | 'lock'
  | 'clock'
  | 'share'
  | 'quota'
  | 'send'
  | 'close'
  | 'arrow'
  | 'plus'
  | 'play'
  | 'sun'
  | 'heart'
  | 'leaf'
  | 'help';

const iconGlyphs: Record<ParentIconName, string> = {
  back: '‹',
  home: '⌂',
  history: '◷',
  notifications: '♧',
  settings: '⚙',
  child: '◉',
  book: '▤',
  camera: '▣',
  voice: '≈',
  spark: '✦',
  check: '✓',
  lock: '⌑',
  clock: '◷',
  share: '↗',
  quota: '◌',
  send: '➤',
  close: '×',
  arrow: '→',
  plus: '+',
  play: '▶',
  sun: '☼',
  heart: '♡',
  leaf: '❧',
  help: '?',
};

export function ParentIcon({
  name,
  size = 20,
  color = sketchColors.green,
}: Readonly<{name: ParentIconName; size?: number; color?: string}>): React.JSX.Element {
  return (
    <Text accessible={false} style={{color, fontSize: size, fontWeight: '700', lineHeight: size + 4}}>
      {iconGlyphs[name]}
    </Text>
  );
}

export function ParentCard({
  children,
  style,
  tone = 'surface',
}: Readonly<{
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
  tone?: 'surface' | 'green' | 'gold' | 'muted';
}>): React.JSX.Element {
  const backgroundColor =
    tone === 'green'
      ? sketchColors.greenSoft
      : tone === 'gold'
        ? sketchColors.goldSoft
        : tone === 'muted'
          ? sketchColors.surfaceMuted
          : sketchColors.surface;

  return <View style={[styles.card, {backgroundColor}, style]}>{children}</View>;
}

export function ScreenIntro({
  eyebrow,
  title,
  description,
}: Readonly<{eyebrow: string; title: string; description?: string}>): React.JSX.Element {
  return (
    <View style={styles.intro}>
      <Text style={styles.eyebrow}>{eyebrow}</Text>
      <Text accessibilityRole="header" style={styles.title}>{title}</Text>
      {description ? <Text style={styles.description}>{description}</Text> : null}
    </View>
  );
}

export function ParentPage({
  children,
  contentStyle,
}: Readonly<{children: ReactNode; contentStyle?: StyleProp<ViewStyle>}>): React.JSX.Element {
  return (
    <ScrollView
      contentContainerStyle={[styles.pageContent, contentStyle]}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}>
      <View style={styles.pageInner}>{children}</View>
    </ScrollView>
  );
}

export function ParentSectionHeading({
  eyebrow,
  title,
  action,
  onAction,
}: Readonly<{eyebrow?: string; title: string; action?: string; onAction?: () => void}>): React.JSX.Element {
  return (
    <View style={styles.sectionHeading}>
      <View style={styles.sectionHeadingCopy}>
        {eyebrow ? <Text style={styles.sectionEyebrow}>{eyebrow}</Text> : null}
        <Text accessibilityRole="header" style={styles.sectionTitle}>{title}</Text>
      </View>
      {action && onAction ? (
        <Pressable accessibilityRole="button" onPress={onAction} style={styles.sectionAction}>
          <Text style={styles.sectionActionLabel}>{action}</Text>
          <ParentIcon name="arrow" size={15} />
        </Pressable>
      ) : null}
    </View>
  );
}

export function ParentButton({
  title,
  onPress,
  icon,
  variant = 'primary',
  disabled = false,
  accessibilityHint,
}: Readonly<{
  title: string;
  onPress: () => void;
  icon?: ParentIconName;
  variant?: 'primary' | 'secondary' | 'quiet' | 'danger';
  disabled?: boolean;
  accessibilityHint?: string;
}>): React.JSX.Element {
  const buttonStyle =
    variant === 'primary'
      ? styles.buttonPrimary
      : variant === 'danger'
        ? styles.buttonDanger
        : variant === 'quiet'
          ? styles.buttonQuiet
          : styles.buttonSecondary;
  const labelStyle =
    variant === 'primary' || variant === 'danger'
      ? styles.buttonLabelLight
      : styles.buttonLabelDark;
  const iconColor = variant === 'primary' || variant === 'danger' ? sketchColors.white : sketchColors.green;

  return (
    <Pressable
      accessibilityHint={accessibilityHint}
      accessibilityRole="button"
      accessibilityState={{disabled}}
      android_ripple={{color: variant === 'primary' ? '#FFFFFF24' : '#24745B18', borderless: false}}
      disabled={disabled}
      onPress={onPress}
      style={({pressed}) => [
        styles.button,
        buttonStyle,
        pressed && !disabled ? styles.buttonPressed : undefined,
        disabled ? styles.buttonDisabled : undefined,
      ]}>
      {icon ? <ParentIcon name={icon} color={iconColor} size={18} /> : null}
      <Text style={[styles.buttonLabel, labelStyle]}>{title}</Text>
    </Pressable>
  );
}

export function ParentField({
  label,
  value,
  onChangeText,
  placeholder,
  helper,
  style,
  ...inputProps
}: Readonly<{
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder?: string;
  helper?: string;
} & TextInputProps>): React.JSX.Element {
  return (
    <View style={styles.fieldWrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={sketchColors.muted}
        style={[styles.input, inputProps.multiline ? styles.inputMultiline : undefined, style]}
        value={value}
        {...inputProps}
      />
      {helper ? <Text style={styles.fieldHelper}>{helper}</Text> : null}
    </View>
  );
}

export function ParentToggleRow({
  title,
  description,
  value,
  onValueChange,
}: Readonly<{
  title: string;
  description: string;
  value: boolean;
  onValueChange: (value: boolean) => void;
}>): React.JSX.Element {
  return (
    <View style={styles.toggleRow}>
      <View style={styles.toggleCopy}>
        <Text style={styles.toggleTitle}>{title}</Text>
        <Text style={styles.toggleDescription}>{description}</Text>
      </View>
      <Switch
        accessibilityLabel={title}
        onValueChange={onValueChange}
        thumbColor={sketchColors.white}
        trackColor={{false: '#CCD7CF', true: sketchColors.green}}
        value={value}
      />
    </View>
  );
}

export function ParentPill({
  label,
  tone = 'green',
}: Readonly<{label: string; tone?: 'green' | 'gold' | 'blue' | 'coral' | 'gray'}>): React.JSX.Element {
  const backgroundColor =
    tone === 'gold'
      ? sketchColors.goldSoft
      : tone === 'blue'
        ? sketchColors.blueSoft
        : tone === 'coral'
          ? sketchColors.coralSoft
          : tone === 'gray'
            ? '#EEF0EB'
            : sketchColors.greenSoft;
  const color =
    tone === 'gold'
      ? '#806218'
      : tone === 'blue'
        ? '#426C87'
        : tone === 'coral'
          ? '#995140'
          : tone === 'gray'
            ? sketchColors.muted
            : sketchColors.greenDark;

  return (
    <View style={[styles.pill, {backgroundColor}]}>
      <Text style={[styles.pillText, {color}]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: sketchSpace.lg,
    borderColor: sketchColors.line,
    borderWidth: 1,
    borderRadius: sketchRadius.md,
    ...sketchShadow,
  },
  intro: {gap: 7, marginBottom: sketchSpace.lg},
  eyebrow: {color: sketchColors.green, fontSize: 10, fontWeight: '800', letterSpacing: 1.4},
  title: {color: sketchColors.ink, fontSize: 27, lineHeight: 33, fontWeight: '800', letterSpacing: -0.6},
  description: {maxWidth: 560, color: sketchColors.muted, fontSize: 14, lineHeight: 21},
  pageContent: {flexGrow: 1, paddingBottom: 24},
  pageInner: {width: '100%', maxWidth: 620, alignSelf: 'center', paddingHorizontal: sketchSpace.lg, paddingTop: sketchSpace.md, gap: 16},
  sectionHeading: {flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', gap: 10, marginTop: 3},
  sectionHeadingCopy: {flex: 1, gap: 3},
  sectionEyebrow: {color: sketchColors.muted, fontSize: 10, fontWeight: '900', letterSpacing: 1.1},
  sectionTitle: {color: sketchColors.ink, fontSize: 17, lineHeight: 23, fontWeight: '900'},
  sectionAction: {minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 4, paddingLeft: 8},
  sectionActionLabel: {color: sketchColors.green, fontSize: 11, fontWeight: '800'},
  button: {
    minHeight: 48,
    paddingHorizontal: sketchSpace.lg,
    borderRadius: sketchRadius.sm,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 9,
  },
  buttonPrimary: {backgroundColor: sketchColors.green, elevation: 3, shadowColor: sketchColors.greenDark, shadowOpacity: 0.14, shadowRadius: 8, shadowOffset: {width: 0, height: 3}},
  buttonSecondary: {backgroundColor: sketchColors.surface, borderWidth: 1, borderColor: sketchColors.line},
  buttonQuiet: {backgroundColor: 'transparent'},
  buttonDanger: {backgroundColor: sketchColors.coral},
  buttonPressed: {opacity: 0.94, elevation: 1, transform: [{translateY: 1}, {scale: 0.99}]},
  buttonDisabled: {opacity: 0.5},
  buttonLabel: {fontSize: 13, fontWeight: '800', textAlign: 'center'},
  buttonLabelLight: {color: sketchColors.white},
  buttonLabelDark: {color: sketchColors.greenDark},
  fieldWrap: {gap: 7},
  fieldLabel: {color: sketchColors.ink, fontSize: 12, fontWeight: '700'},
  input: {
    minHeight: 48,
    paddingHorizontal: 13,
    paddingVertical: 11,
    borderWidth: 1,
    borderColor: sketchColors.line,
    borderRadius: sketchRadius.sm,
    backgroundColor: sketchColors.surface,
    color: sketchColors.ink,
    fontSize: 14,
  },
  inputMultiline: {minHeight: 96, textAlignVertical: 'top'},
  fieldHelper: {color: sketchColors.muted, fontSize: 11, lineHeight: 16},
  toggleRow: {flexDirection: 'row', alignItems: 'center', gap: 12},
  toggleCopy: {flex: 1, gap: 4},
  toggleTitle: {color: sketchColors.ink, fontSize: 13, fontWeight: '700'},
  toggleDescription: {color: sketchColors.muted, fontSize: 11, lineHeight: 16},
  pill: {alignSelf: 'flex-start', paddingHorizontal: 10, paddingVertical: 6, borderRadius: sketchRadius.pill},
  pillText: {fontSize: 10, fontWeight: '800'},
});
