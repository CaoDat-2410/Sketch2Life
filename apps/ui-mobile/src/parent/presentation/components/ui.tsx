import React, { type PropsWithChildren, useState } from 'react';
import { ActivityIndicator, Image, Modal, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View, type TextInputProps } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import Svg, { Path } from 'react-native-svg';

export const palette = {
  ink: '#342E28',
  muted: '#5B5148',
  blue: '#1F5D8F',
  paleBlue: '#DDEBFA',
  background: '#FFF8EA',
  white: '#FFFEF8',
  border: '#493A2F',
  green: '#234D2A',
  paleGreen: '#DDF1D8',
  amber: '#5A4100',
  paleAmber: '#FFF0B8',
  red: '#5B211A',
  paleRed: '#F7D7CF',
  outline: '#493A2F',
  action: '#493A2F',
  actionText: '#FFFEF8',
  dangerFill: '#702F2A',
  disabledSurface: '#EAE4D9',
  disabledText: '#4D473F',
  info: '#254B69',
  success: '#234D2A',
  warning: '#5A4100',
  error: '#5B211A',
  focus: '#1F5D8F',
  mint: '#DDF1D8',
  butter: '#FFF0B8',
  lilac: '#E9DEF7',
  playerGate: '#F0EBE1',
  crayonMarker: '#9B5A19',
};

const touchTargets = {
  minimum: 44,
  primary: 52,
  navigation: 52,
} as const;

const outlineWidths = {
  control: 1.5,
  card: 1.6,
  primary: 2,
  focus: 3,
} as const;

const contrastPairs = [
  { name: 'Body text on warm paper', foreground: palette.ink, background: palette.background, minimumRatio: 4.5 },
  { name: 'Body text on card white', foreground: palette.ink, background: palette.white, minimumRatio: 4.5 },
  { name: 'Secondary copy on warm paper', foreground: palette.muted, background: palette.background, minimumRatio: 4.5 },
  { name: 'Secondary copy on card white', foreground: palette.muted, background: palette.white, minimumRatio: 4.5 },
  { name: 'Primary button label', foreground: palette.actionText, background: palette.action, minimumRatio: 4.5 },
  { name: 'Destructive button label', foreground: palette.actionText, background: palette.dangerFill, minimumRatio: 4.5 },
  { name: 'Disabled control label', foreground: palette.disabledText, background: palette.disabledSurface, minimumRatio: 4.5 },
  { name: 'Busy indicator on disabled surface', foreground: palette.disabledText, background: palette.disabledSurface, minimumRatio: 4.5 },
  { name: 'Information text and icon', foreground: palette.info, background: palette.paleBlue, minimumRatio: 4.5 },
  { name: 'Success text and icon', foreground: palette.success, background: palette.paleGreen, minimumRatio: 4.5 },
  { name: 'Warning text and icon', foreground: palette.warning, background: palette.paleAmber, minimumRatio: 4.5 },
  { name: 'Error text and icon', foreground: palette.error, background: palette.paleRed, minimumRatio: 4.5 },
  { name: 'Error helper text on card', foreground: palette.error, background: palette.white, minimumRatio: 4.5 },
  { name: 'Error text on warm paper', foreground: palette.error, background: palette.background, minimumRatio: 4.5 },
  { name: 'Ink on selected mint surface', foreground: palette.ink, background: palette.mint, minimumRatio: 4.5 },
  { name: 'Ink on stage-status sky surface', foreground: palette.ink, background: palette.paleBlue, minimumRatio: 4.5 },
  { name: 'Ink on warm sticker', foreground: palette.ink, background: palette.butter, minimumRatio: 4.5 },
  { name: 'Ink on optional lilac cue', foreground: palette.ink, background: palette.lilac, minimumRatio: 4.5 },
  { name: 'Ink on player gate', foreground: palette.ink, background: palette.playerGate, minimumRatio: 4.5 },
  { name: 'Secondary copy on player gate', foreground: palette.muted, background: palette.playerGate, minimumRatio: 4.5 },
  { name: 'Secondary copy on selected mint surface', foreground: palette.muted, background: palette.mint, minimumRatio: 4.5 },
  { name: 'Secondary copy on pressed sky surface', foreground: palette.muted, background: palette.paleBlue, minimumRatio: 4.5 },
  { name: 'Action accent on warm paper', foreground: palette.blue, background: palette.background, minimumRatio: 4.5 },
  { name: 'Action accent on card white', foreground: palette.blue, background: palette.white, minimumRatio: 4.5 },
  { name: 'Action accent on selected sky', foreground: palette.blue, background: palette.paleBlue, minimumRatio: 4.5 },
  { name: 'Selected navigation icon on warm sticker', foreground: palette.blue, background: palette.butter, minimumRatio: 3 },
  { name: 'Selected navigation outline on warm sticker', foreground: palette.outline, background: palette.butter, minimumRatio: 3 },
  { name: 'Focus ring against card', foreground: palette.focus, background: palette.white, minimumRatio: 3 },
  { name: 'Focus ring against warm paper', foreground: palette.focus, background: palette.background, minimumRatio: 3 },
  { name: 'Focus ring against selected mint', foreground: palette.focus, background: palette.mint, minimumRatio: 3 },
  { name: 'Focus ring against pressed sky', foreground: palette.focus, background: palette.paleBlue, minimumRatio: 3 },
  { name: 'Crayon outline against card', foreground: palette.outline, background: palette.white, minimumRatio: 3 },
  { name: 'Crayon outline against paper', foreground: palette.outline, background: palette.background, minimumRatio: 3 },
  { name: 'Crayon outline against selected mint', foreground: palette.outline, background: palette.mint, minimumRatio: 3 },
  { name: 'Crayon outline against information sky', foreground: palette.outline, background: palette.paleBlue, minimumRatio: 3 },
  { name: 'Crayon outline against success mint', foreground: palette.outline, background: palette.paleGreen, minimumRatio: 3 },
  { name: 'Crayon outline against warning butter', foreground: palette.outline, background: palette.paleAmber, minimumRatio: 3 },
  { name: 'Crayon outline against error coral', foreground: palette.outline, background: palette.paleRed, minimumRatio: 3 },
  { name: 'Crayon marker against warm paper', foreground: palette.crayonMarker, background: palette.background, minimumRatio: 3 },
  { name: 'Crayon marker against card white', foreground: palette.crayonMarker, background: palette.white, minimumRatio: 3 },
] as const;

export function ScreenFrame({
  title,
  subtitle,
  step,
  onBack,
  backDisabled = false,
  children,
}: PropsWithChildren<{ title: string; subtitle?: string; step?: string; onBack?: () => void; backDisabled?: boolean }>): React.JSX.Element {
  const [backFocused, setBackFocused] = useState(false);

  return (
    <LinearGradient colors={[palette.background, palette.white]} start={{ x: 0, y: 0 }} end={{ x: 0, y: 1 }} style={styles.screen}>
      <View style={styles.topBar}>
        {onBack ? (
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Quay lại"
            accessibilityState={{ disabled: backDisabled }}
            disabled={backDisabled}
            onPress={onBack}
            onFocus={() => setBackFocused(true)}
            onBlur={() => setBackFocused(false)}
            style={[styles.backButton, backDisabled && styles.disabledOutline, backFocused && styles.focusRing]}
          >
            <Ionicons name="arrow-back" size={19} color={palette.ink} accessible={false} />
          </TouchableOpacity>
        ) : (
          <Image
            source={require('../../../../assets/applied/sketch2life-logo.png')}
            style={styles.brandLogo}
            resizeMode="contain"
            accessible={false}
          />
        )}
        <View style={styles.headingBlock}>
          <Text accessibilityRole="header" style={styles.heading}>{title}</Text>
          {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
        </View>
        {step ? <Text style={styles.stepText}>{step}</Text> : null}
      </View>
      <ScrollView style={styles.contentScroll} contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {children}
      </ScrollView>
    </LinearGradient>
  );
}

export function Card({ children, style }: PropsWithChildren<{ style?: object }>): React.JSX.Element {
  return <View style={[styles.card, style, styles.cardEdge]}>{children}</View>;
}

export function PrimaryButton({
  label,
  onPress,
  disabled = false,
  busy = false,
}: { label: string; onPress: () => void; disabled?: boolean; busy?: boolean }): React.JSX.Element {
  const [focused, setFocused] = useState(false);

  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: disabled || busy, busy }}
      onPress={onPress}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      disabled={disabled || busy}
      activeOpacity={0.86}
      style={[styles.primaryButton, (disabled || busy) && styles.disabledButton, focused && styles.focusRing]}
    >
      {busy ? <ActivityIndicator color={palette.disabledText} /> : <Text style={[styles.primaryButtonText, disabled && styles.disabledLabel]}>{label}</Text>}
    </TouchableOpacity>
  );
}

export function SecondaryButton({ label, onPress, disabled = false }: { label: string; onPress: () => void; disabled?: boolean }): React.JSX.Element {
  const [focused, setFocused] = useState(false);

  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
      onPress={onPress}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      disabled={disabled}
      activeOpacity={0.86}
      style={[styles.secondaryButton, disabled && styles.disabledOutline, focused && styles.focusRing]}
    >
      <Text style={[styles.secondaryButtonText, disabled && styles.disabledLabel]}>{label}</Text>
    </TouchableOpacity>
  );
}

export function ConfirmButton({
  label,
  title,
  message,
  confirmLabel,
  onConfirm,
  destructive = false,
}: {
  label: string;
  title: string;
  message: string;
  confirmLabel: string;
  onConfirm: () => void;
  destructive?: boolean;
}): React.JSX.Element {
  const [confirmationVisible, setConfirmationVisible] = useState(false);
  const [focused, setFocused] = useState(false);
  const [confirmFocused, setConfirmFocused] = useState(false);

  return (
    <>
      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel={label}
        onPress={() => setConfirmationVisible(true)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        activeOpacity={0.86}
        style={[styles.textButton, focused && styles.focusRing]}
      >
        <Text style={[styles.textButtonLabel, destructive && styles.destructiveText]}>{label}</Text>
      </TouchableOpacity>
      <Modal
        visible={confirmationVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setConfirmationVisible(false)}
      >
        <View style={styles.confirmOverlay}>
          <View accessible accessibilityRole="alert" accessibilityLabel={title} accessibilityViewIsModal style={styles.confirmDialog}>
            <Text style={styles.confirmTitle}>{title}</Text>
            <Text style={styles.confirmMessage}>{message}</Text>
            <View style={styles.confirmActions}>
              <SecondaryButton label="Quay lại" onPress={() => setConfirmationVisible(false)} />
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel={confirmLabel}
                accessibilityState={{ disabled: false }}
                onPress={() => {
                  setConfirmationVisible(false);
                  onConfirm();
                }}
                onFocus={() => setConfirmFocused(true)}
                onBlur={() => setConfirmFocused(false)}
                activeOpacity={0.86}
                style={[styles.confirmAction, destructive && styles.confirmActionDestructive, confirmFocused && styles.focusRing]}
              >
                <Text style={styles.confirmActionText}>{confirmLabel}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </>
  );
}

export function TextButton({ label, onPress, disabled = false }: { label: string; onPress: () => void; disabled?: boolean }): React.JSX.Element {
  const [focused, setFocused] = useState(false);

  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      activeOpacity={0.86}
      style={[styles.textButton, focused && styles.focusRing]}
    >
      <Text style={[styles.textButtonLabel, disabled && styles.disabledLabel]}>{label}</Text>
    </TouchableOpacity>
  );
}

export function Field({ label, multiline, style, onFocus, onBlur, accessibilityLabel, ...props }: TextInputProps & { label: string }): React.JSX.Element {
  const [focused, setFocused] = useState(false);

  return (
    <View style={styles.fieldWrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        {...props}
        accessibilityLabel={accessibilityLabel ?? label}
        multiline={multiline}
        onFocus={(event) => {
          setFocused(true);
          onFocus?.(event);
        }}
        onBlur={(event) => {
          setFocused(false);
          onBlur?.(event);
        }}
        placeholderTextColor={palette.muted}
        selectionColor={palette.focus}
        style={[styles.field, multiline && styles.multilineField, focused && styles.fieldFocused, style]}
      />
    </View>
  );
}

export function Notice({ text, tone = 'info' }: { text: string; tone?: 'info' | 'success' | 'warning' | 'error' }): React.JSX.Element {
  const toneStyle = tone === 'success' ? styles.noticeSuccess : tone === 'warning' ? styles.noticeWarning : tone === 'error' ? styles.noticeError : styles.noticeInfo;
  const toneTextStyle = tone === 'success' ? styles.noticeSuccessText : tone === 'warning' ? styles.noticeWarningText : tone === 'error' ? styles.noticeErrorText : styles.noticeInfoText;
  const iconName = tone === 'success' ? 'checkmark-circle-outline' : tone === 'warning' ? 'warning-outline' : tone === 'error' ? 'alert-circle-outline' : 'information-circle-outline';
  const iconColor = tone === 'success' ? palette.success : tone === 'warning' ? palette.warning : tone === 'error' ? palette.error : palette.info;

  return (
    <View accessible accessibilityRole={tone === 'error' ? 'alert' : 'summary'} style={[styles.notice, toneStyle]}>
      <Ionicons name={iconName} size={17} color={iconColor} accessible={false} />
      <Text style={[styles.noticeText, toneTextStyle]}>{text}</Text>
    </View>
  );
}

export function SectionTitle({ children }: PropsWithChildren): React.JSX.Element {
  return (
    <View style={styles.sectionTitleWrap}>
      <Text accessibilityRole="header" style={styles.sectionTitle}>{children}</Text>
      <Svg width={48} height={9} viewBox="0 0 48 9" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        <Path d="M2 5 C13 2, 29 8, 46 4" fill="none" stroke={palette.crayonMarker} strokeWidth={outlineWidths.primary} strokeLinecap="round" />
      </Svg>
    </View>
  );
}

export function ChoiceRow({ title, detail, selected, onPress }: { title: string; detail?: string; selected?: boolean; onPress: () => void }): React.JSX.Element {
  const [focused, setFocused] = useState(false);

  return (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={detail ? `${title}. ${detail}` : title}
      accessibilityState={{ selected }}
      onPress={onPress}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      activeOpacity={0.88}
      style={[styles.choice, selected && styles.choiceSelected, focused && styles.focusRing]}
    >
      <View style={styles.choiceCopy}>
        <Text style={styles.choiceTitle}>{title}</Text>
        {detail ? <Text style={styles.choiceDetail}>{detail}</Text> : null}
      </View>
      <View style={[styles.choiceMark, selected && styles.choiceMarkSelected]}>{selected ? <Text style={styles.choiceCheck}>✓</Text> : null}</View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background },
  topBar: { minHeight: 72, paddingHorizontal: 16, paddingVertical: 10, flexDirection: 'row', alignItems: 'center', gap: 9, borderBottomWidth: 1, borderBottomColor: palette.outline, backgroundColor: palette.background },
  brandLogo: { width: 48, height: 48 },
  backButton: { width: touchTargets.minimum, height: touchTargets.minimum, borderRadius: 999, borderWidth: outlineWidths.control, borderColor: palette.outline, backgroundColor: palette.paleBlue, alignItems: 'center', justifyContent: 'center' },
  headingBlock: { flex: 1, minWidth: 0, gap: 3 },
  heading: { color: palette.ink, fontSize: 19, lineHeight: 22, fontWeight: '800', minWidth: 0, flexShrink: 1 },
  subtitle: { color: palette.muted, fontSize: 11, lineHeight: 15, minWidth: 0, flexShrink: 1 },
  stepText: { color: palette.ink, fontSize: 9, lineHeight: 12, fontWeight: '800', minWidth: 0, maxWidth: 96, flexShrink: 1, textAlign: 'center', paddingHorizontal: 7, paddingVertical: 5, borderWidth: 1, borderColor: palette.outline, borderTopLeftRadius: 10, borderTopRightRadius: 12, borderBottomRightRadius: 9, borderBottomLeftRadius: 11, backgroundColor: palette.lilac, overflow: 'hidden' },
  contentScroll: { flex: 1, minHeight: 0 },
  scrollContent: { width: '100%', maxWidth: 520, alignSelf: 'center', paddingHorizontal: 15, paddingTop: 14, paddingBottom: 18, gap: 11 },
  card: { backgroundColor: palette.white, padding: 13, gap: 12, shadowColor: palette.ink, shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.09, shadowRadius: 18, elevation: 3 },
  cardEdge: { borderWidth: outlineWidths.card, borderColor: palette.outline, borderTopLeftRadius: 22, borderTopRightRadius: 25, borderBottomRightRadius: 19, borderBottomLeftRadius: 23 },
  primaryButton: { minHeight: touchTargets.primary, borderTopLeftRadius: 14, borderTopRightRadius: 16, borderBottomRightRadius: 13, borderBottomLeftRadius: 15, borderWidth: outlineWidths.primary, borderColor: palette.outline, backgroundColor: palette.ink, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 9, shadowColor: palette.ink, shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.08, shadowRadius: 9, elevation: 2 },
  primaryButtonText: { color: palette.white, fontSize: 13, lineHeight: 18, fontWeight: '800', textAlign: 'center', flexShrink: 1 },
  disabledButton: { backgroundColor: palette.disabledSurface, borderColor: palette.outline },
  disabledLabel: { color: palette.disabledText },
  secondaryButton: { minHeight: 48, borderTopLeftRadius: 14, borderTopRightRadius: 16, borderBottomRightRadius: 13, borderBottomLeftRadius: 15, borderColor: palette.outline, borderWidth: 1.8, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 9, backgroundColor: palette.white },
  secondaryButtonText: { color: palette.ink, fontSize: 13, lineHeight: 18, fontWeight: '800', textAlign: 'center', flexShrink: 1 },
  disabledOutline: { backgroundColor: palette.disabledSurface, borderColor: palette.outline },
  focusRing: { borderColor: palette.focus, borderWidth: outlineWidths.focus, shadowColor: palette.focus, shadowOpacity: 0.18, shadowRadius: 3, elevation: 3 },
  textButton: { minHeight: touchTargets.minimum, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 10, borderRadius: 12 },
  textButtonLabel: { color: palette.blue, fontSize: 13, lineHeight: 18, fontWeight: '700', textAlign: 'center', flexShrink: 1 },
  destructiveText: { color: palette.error },
  confirmOverlay: { flex: 1, backgroundColor: 'rgba(52,46,40,0.44)', alignItems: 'center', justifyContent: 'center', padding: 24 },
  confirmDialog: { width: '100%', maxWidth: 420, borderWidth: outlineWidths.card, borderColor: palette.outline, borderTopLeftRadius: 21, borderTopRightRadius: 24, borderBottomRightRadius: 19, borderBottomLeftRadius: 22, padding: 14, gap: 12, backgroundColor: palette.white, shadowColor: palette.ink, shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.09, shadowRadius: 18, elevation: 5 },
  confirmTitle: { color: palette.ink, fontSize: 17, lineHeight: 22, fontWeight: '800', flexShrink: 1 },
  confirmMessage: { color: palette.muted, fontSize: 12, lineHeight: 17, flexShrink: 1 },
  confirmActions: { flexDirection: 'row', gap: 8, marginTop: 6 },
  confirmAction: { flex: 1, minWidth: 0, minHeight: touchTargets.primary, borderTopLeftRadius: 14, borderTopRightRadius: 16, borderBottomRightRadius: 13, borderBottomLeftRadius: 15, borderWidth: outlineWidths.primary, borderColor: palette.outline, backgroundColor: palette.ink, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 8, paddingVertical: 9 },
  confirmActionDestructive: { backgroundColor: palette.dangerFill },
  confirmActionText: { color: palette.white, fontSize: 12, lineHeight: 16, fontWeight: '800', textAlign: 'center', flexShrink: 1 },
  fieldWrap: { gap: 4, minWidth: 0 },
  fieldLabel: { color: palette.ink, fontSize: 12, lineHeight: 16, fontWeight: '700', flexShrink: 1 },
  field: { borderWidth: 1.4, borderColor: palette.outline, borderRadius: 12, minHeight: 44, paddingHorizontal: 10, paddingVertical: 9, color: palette.ink, backgroundColor: palette.white, fontSize: 13, flexShrink: 1 },
  fieldFocused: { borderWidth: outlineWidths.focus, borderColor: palette.focus, shadowColor: palette.focus, shadowOpacity: 0.18, shadowRadius: 3, elevation: 2 },
  multilineField: { minHeight: 68, paddingTop: 9, textAlignVertical: 'top' },
  notice: { minHeight: touchTargets.minimum, paddingHorizontal: 10, paddingVertical: 9, borderTopLeftRadius: 13, borderTopRightRadius: 15, borderBottomRightRadius: 12, borderBottomLeftRadius: 14, borderWidth: 1.4, borderColor: palette.outline, flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  noticeInfo: { backgroundColor: palette.paleBlue },
  noticeSuccess: { backgroundColor: palette.paleGreen },
  noticeWarning: { backgroundColor: palette.paleAmber },
  noticeError: { backgroundColor: palette.paleRed },
  noticeText: { flex: 1, minWidth: 0, flexShrink: 1, fontSize: 11, lineHeight: 15 },
  noticeInfoText: { color: palette.info },
  noticeSuccessText: { color: palette.success },
  noticeWarningText: { color: palette.warning },
  noticeErrorText: { color: palette.error },
  sectionTitleWrap: { alignSelf: 'flex-start', maxWidth: '100%', minWidth: 0, flexShrink: 1, gap: 2 },
  sectionTitle: { color: palette.ink, fontSize: 16, lineHeight: 20, fontWeight: '800', marginBottom: 2, minWidth: 0, flexShrink: 1 },
  choice: { minHeight: 60, minWidth: 0, padding: 8, borderRadius: 12, borderWidth: 1.3, borderColor: palette.outline, backgroundColor: palette.white, flexDirection: 'row', alignItems: 'center', gap: 8, shadowColor: palette.ink, shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.08, shadowRadius: 9, elevation: 1 },
  choiceSelected: { borderWidth: 2, borderColor: palette.outline, backgroundColor: palette.mint },
  choiceCopy: { flex: 1, minWidth: 0, flexShrink: 1, gap: 2 },
  choiceTitle: { color: palette.ink, fontSize: 12, lineHeight: 16, fontWeight: '700', flexShrink: 1 },
  choiceDetail: { color: palette.muted, fontSize: 10, lineHeight: 13, flexShrink: 1 },
  choiceMark: { width: 21, height: 21, borderWidth: 1.7, borderColor: palette.outline, borderRadius: 11, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.white },
  choiceMarkSelected: { borderColor: palette.outline, backgroundColor: palette.action },
  choiceCheck: { color: palette.actionText, fontSize: 13, fontWeight: '900' },
});
