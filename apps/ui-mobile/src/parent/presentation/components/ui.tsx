import React, { type PropsWithChildren, useState } from 'react';
import { ActivityIndicator, Modal, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View, type TextInputProps } from 'react-native';
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
            <Text style={styles.backText}>‹</Text>
          </TouchableOpacity>
        ) : (
          <View style={styles.brandDot}><Text style={styles.brandDotText}>S</Text></View>
        )}
        <View style={styles.brandBlock}><Text style={styles.brand}>Sketch2Life</Text>{step ? <Text style={styles.stepText}>{step}</Text> : null}</View>
      </View>
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        <View style={styles.headingBlock}>
          <Text accessibilityRole="header" style={styles.heading}>{title}</Text>
          <Svg width={72} height={12} viewBox="0 0 72 12" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
            <Path d="M3 7 C18 3, 38 11, 68 5" fill="none" stroke={palette.crayonMarker} strokeWidth={3} strokeLinecap="round" />
          </Svg>
          {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
        </View>
        {children}
      </ScrollView>
    </LinearGradient>
  );
}

export function Card({ children, style }: PropsWithChildren<{ style?: object }>): React.JSX.Element {
  return <View style={[styles.card, style]}>{children}</View>;
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
      <Ionicons name={iconName} size={20} color={iconColor} accessible={false} />
      <Text style={[styles.noticeText, toneTextStyle]}>{text}</Text>
    </View>
  );
}

export function SectionTitle({ children }: PropsWithChildren): React.JSX.Element {
  return (
    <View style={styles.sectionTitleWrap}>
      <Text accessibilityRole="header" style={styles.sectionTitle}>{children}</Text>
      <Svg width={48} height={9} viewBox="0 0 48 9" accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        <Path d="M2 5 C13 2, 29 8, 46 4" fill="none" stroke={palette.crayonMarker} strokeWidth={2.5} strokeLinecap="round" />
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
  topBar: { minHeight: 68, paddingHorizontal: 20, flexDirection: 'row', alignItems: 'center', gap: 12, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: palette.outline, backgroundColor: palette.white },
  brandDot: { width: 42, height: 42, borderRadius: 16, borderWidth: 2, borderColor: palette.outline, backgroundColor: palette.butter, alignItems: 'center', justifyContent: 'center' },
  brandDotText: { color: palette.ink, fontSize: 17, fontWeight: '800' },
  brandBlock: { flex: 1, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  brand: { color: palette.ink, fontSize: 15, fontWeight: '800', letterSpacing: 0.1 },
  stepText: { color: palette.muted, fontSize: 12, fontWeight: '700' },
  backButton: { width: touchTargets.minimum, height: touchTargets.minimum, borderRadius: 15, borderWidth: 1.5, borderColor: palette.outline, backgroundColor: palette.paleBlue, alignItems: 'center', justifyContent: 'center' },
  backText: { color: palette.blue, fontSize: 30, lineHeight: 32, marginTop: -4 },
  scrollContent: { width: '100%', maxWidth: 520, alignSelf: 'center', paddingHorizontal: 20, paddingTop: 24, paddingBottom: 34, gap: 16 },
  headingBlock: { gap: 6, marginBottom: 4 },
  heading: { color: palette.ink, fontSize: 26, lineHeight: 32, fontWeight: '800' },
  subtitle: { color: palette.muted, fontSize: 15, lineHeight: 22 },
  card: { backgroundColor: palette.white, borderColor: palette.outline, borderWidth: 1.6, borderRadius: 22, padding: 16, gap: 12, shadowColor: palette.ink, shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.09, shadowRadius: 18, elevation: 3 },
  primaryButton: { minHeight: touchTargets.primary, borderRadius: 15, borderWidth: 2, borderColor: palette.outline, backgroundColor: palette.action, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 18, shadowColor: palette.ink, shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.08, shadowRadius: 9, elevation: 2 },
  primaryButtonText: { color: palette.actionText, fontSize: 16, fontWeight: '800' },
  disabledButton: { backgroundColor: palette.disabledSurface, borderColor: palette.outline },
  disabledLabel: { color: palette.disabledText },
  secondaryButton: { minHeight: 48, borderRadius: 15, borderColor: palette.outline, borderWidth: 1.5, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 18, backgroundColor: palette.white },
  secondaryButtonText: { color: palette.blue, fontSize: 15, fontWeight: '800' },
  disabledOutline: { backgroundColor: palette.disabledSurface, borderColor: palette.outline },
  focusRing: { borderColor: palette.focus, borderWidth: 3, shadowColor: palette.focus, shadowOpacity: 0.18, shadowRadius: 3, elevation: 3 },
  textButton: { minHeight: touchTargets.minimum, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 10, borderRadius: 12 },
  textButtonLabel: { color: palette.blue, fontSize: 14, fontWeight: '700' },
  destructiveText: { color: palette.error },
  confirmOverlay: { flex: 1, backgroundColor: 'rgba(52,46,40,0.44)', alignItems: 'center', justifyContent: 'center', padding: 24 },
  confirmDialog: { width: '100%', maxWidth: 420, borderWidth: 1.6, borderColor: palette.outline, borderRadius: 22, padding: 22, gap: 12, backgroundColor: palette.white, shadowColor: palette.ink, shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.09, shadowRadius: 18, elevation: 5 },
  confirmTitle: { color: palette.ink, fontSize: 19, fontWeight: '800' },
  confirmMessage: { color: palette.muted, fontSize: 15, lineHeight: 22 },
  confirmActions: { flexDirection: 'row', gap: 10, marginTop: 6 },
  confirmAction: { flex: 1, minHeight: 48, borderRadius: 15, borderWidth: 2, borderColor: palette.outline, backgroundColor: palette.action, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 14 },
  confirmActionDestructive: { backgroundColor: palette.dangerFill },
  confirmActionText: { color: palette.actionText, fontSize: 15, fontWeight: '800' },
  fieldWrap: { gap: 7 },
  fieldLabel: { color: palette.ink, fontSize: 13, fontWeight: '700' },
  field: { borderWidth: 1.5, borderColor: palette.outline, borderRadius: 15, minHeight: 48, paddingHorizontal: 13, color: palette.ink, backgroundColor: palette.white, fontSize: 15 },
  fieldFocused: { borderWidth: 3, borderColor: palette.focus, shadowColor: palette.focus, shadowOpacity: 0.18, shadowRadius: 3, elevation: 2 },
  multilineField: { minHeight: 84, paddingTop: 12, textAlignVertical: 'top' },
  notice: { minHeight: touchTargets.minimum, padding: 13, borderRadius: 15, borderWidth: 1.5, borderColor: palette.outline, flexDirection: 'row', alignItems: 'flex-start', gap: 9 },
  noticeInfo: { backgroundColor: palette.paleBlue },
  noticeSuccess: { backgroundColor: palette.paleGreen },
  noticeWarning: { backgroundColor: palette.paleAmber },
  noticeError: { backgroundColor: palette.paleRed },
  noticeText: { flex: 1, fontSize: 14, lineHeight: 20 },
  noticeInfoText: { color: palette.info },
  noticeSuccessText: { color: palette.success },
  noticeWarningText: { color: palette.warning },
  noticeErrorText: { color: palette.error },
  sectionTitleWrap: { alignSelf: 'flex-start', gap: 2 },
  sectionTitle: { color: palette.ink, fontSize: 16, fontWeight: '800', marginBottom: 2 },
  choice: { minHeight: 56, padding: 13, borderRadius: 16, borderWidth: 1.5, borderColor: palette.outline, backgroundColor: palette.white, flexDirection: 'row', alignItems: 'center', gap: 12, shadowColor: palette.ink, shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.08, shadowRadius: 9, elevation: 1 },
  choiceSelected: { borderColor: palette.outline, backgroundColor: palette.mint },
  choiceCopy: { flex: 1, gap: 3 },
  choiceTitle: { color: palette.ink, fontSize: 15, fontWeight: '700' },
  choiceDetail: { color: palette.muted, fontSize: 13, lineHeight: 18 },
  choiceMark: { width: 24, height: 24, borderWidth: 1.5, borderColor: palette.outline, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.white },
  choiceMarkSelected: { borderColor: palette.outline, backgroundColor: palette.action },
  choiceCheck: { color: palette.actionText, fontSize: 13, fontWeight: '900' },
});
