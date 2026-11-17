import React, { type PropsWithChildren, useState } from 'react';
import { ActivityIndicator, Modal, ScrollView, StatusBar, StyleSheet, Text, TextInput, TouchableOpacity, View, type TextInputProps } from 'react-native';

export const palette = {
  ink: '#172B4D',
  muted: '#66758A',
  blue: '#1D63F2',
  paleBlue: '#EFF6FF',
  background: '#F6F9FC',
  white: '#FFFFFF',
  border: '#DCE5EF',
  green: '#16845B',
  paleGreen: '#EAF8F1',
  amber: '#986100',
  paleAmber: '#FFF6DF',
  red: '#B42318',
  paleRed: '#FEF0EF',
};

export function ScreenFrame({
  title,
  subtitle,
  step,
  onBack,
  backDisabled = false,
  children,
}: PropsWithChildren<{ title: string; subtitle?: string; step?: string; onBack?: () => void; backDisabled?: boolean }>): React.JSX.Element {
  return (
    <View style={styles.screen}>
      <View style={styles.topBar}>
        {onBack ? <TouchableOpacity accessibilityRole="button" accessibilityState={{ disabled: backDisabled }} disabled={backDisabled} onPress={onBack} style={[styles.backButton, backDisabled && styles.disabledOutline]}><Text style={styles.backText}>‹</Text></TouchableOpacity> : <View style={styles.brandDot}><Text style={styles.brandDotText}>S</Text></View>}
        <View style={styles.brandBlock}><Text style={styles.brand}>Sketch2Life</Text>{step ? <Text style={styles.stepText}>{step}</Text> : null}</View>
      </View>
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        <View style={styles.headingBlock}>
          <Text style={styles.heading}>{title}</Text>
          {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
        </View>
        {children}
      </ScrollView>
    </View>
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
  return (
    <TouchableOpacity accessibilityRole="button" accessibilityState={{ disabled: disabled || busy }} onPress={onPress} disabled={disabled || busy} style={[styles.primaryButton, (disabled || busy) && styles.disabledButton]}>
      {busy ? <ActivityIndicator color={palette.white} /> : <Text style={styles.primaryButtonText}>{label}</Text>}
    </TouchableOpacity>
  );
}

export function SecondaryButton({ label, onPress, disabled = false }: { label: string; onPress: () => void; disabled?: boolean }): React.JSX.Element {
  return <TouchableOpacity accessibilityRole="button" onPress={onPress} disabled={disabled} style={[styles.secondaryButton, disabled && styles.disabledOutline]}><Text style={styles.secondaryButtonText}>{label}</Text></TouchableOpacity>;
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

  return (
    <>
      <TouchableOpacity
        accessibilityRole="button"
        onPress={() => setConfirmationVisible(true)}
        style={styles.textButton}
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
          <View accessible accessibilityLabel={title} style={styles.confirmDialog}>
            <Text style={styles.confirmTitle}>{title}</Text>
            <Text style={styles.confirmMessage}>{message}</Text>
            <View style={styles.confirmActions}>
              <SecondaryButton label="Quay lại" onPress={() => setConfirmationVisible(false)} />
              <TouchableOpacity
                accessibilityRole="button"
                onPress={() => {
                  setConfirmationVisible(false);
                  onConfirm();
                }}
                style={[styles.confirmAction, destructive && styles.confirmActionDestructive]}
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
  return (
    <TouchableOpacity accessibilityRole="button" disabled={disabled} onPress={onPress} style={styles.textButton}>
      <Text style={[styles.textButtonLabel, disabled && styles.disabledText]}>{label}</Text>
    </TouchableOpacity>
  );
}

export function Field({ label, multiline, style, ...props }: TextInputProps & { label: string }): React.JSX.Element {
  return (
    <View style={styles.fieldWrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        {...props}
        multiline={multiline}
        placeholderTextColor="#8795A8"
        style={[styles.field, multiline && styles.multilineField, style]}
      />
    </View>
  );
}

export function Notice({ text, tone = 'info' }: { text: string; tone?: 'info' | 'success' | 'warning' | 'error' }): React.JSX.Element {
  const toneStyle = tone === 'success' ? styles.noticeSuccess : tone === 'warning' ? styles.noticeWarning : tone === 'error' ? styles.noticeError : styles.noticeInfo;
  return <View style={[styles.notice, toneStyle]}><Text style={styles.noticeText}>{text}</Text></View>;
}

export function SectionTitle({ children }: PropsWithChildren): React.JSX.Element {
  return <Text style={styles.sectionTitle}>{children}</Text>;
}

export function ChoiceRow({ title, detail, selected, onPress }: { title: string; detail?: string; selected?: boolean; onPress: () => void }): React.JSX.Element {
  return (
    <TouchableOpacity accessibilityRole="button" accessibilityState={{ selected }} onPress={onPress} style={[styles.choice, selected && styles.choiceSelected]}>
      <View style={styles.choiceCopy}><Text style={styles.choiceTitle}>{title}</Text>{detail ? <Text style={styles.choiceDetail}>{detail}</Text> : null}</View>
      <View style={[styles.choiceMark, selected && styles.choiceMarkSelected]}>{selected ? <Text style={styles.choiceCheck}>✓</Text> : null}</View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: palette.background, paddingTop: StatusBar.currentHeight ?? 0 },
  topBar: { minHeight: 62, paddingHorizontal: 20, flexDirection: 'row', alignItems: 'center', gap: 12, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: palette.border, backgroundColor: palette.white },
  brandDot: { width: 34, height: 34, borderRadius: 12, backgroundColor: palette.blue, alignItems: 'center', justifyContent: 'center' },
  brandDotText: { color: palette.white, fontSize: 17, fontWeight: '800' },
  brandBlock: { flex: 1, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  brand: { color: palette.ink, fontSize: 15, fontWeight: '800', letterSpacing: 0.1 },
  stepText: { color: palette.muted, fontSize: 12, fontWeight: '700' },
  backButton: { width: 34, height: 34, borderRadius: 12, backgroundColor: palette.paleBlue, alignItems: 'center', justifyContent: 'center' },
  backText: { color: palette.blue, fontSize: 30, lineHeight: 32, marginTop: -4 },
  scrollContent: { width: '100%', maxWidth: 520, alignSelf: 'center', paddingHorizontal: 20, paddingTop: 24, paddingBottom: 34, gap: 16 },
  headingBlock: { gap: 6, marginBottom: 4 },
  heading: { color: palette.ink, fontSize: 26, lineHeight: 32, fontWeight: '800' },
  subtitle: { color: palette.muted, fontSize: 15, lineHeight: 22 },
  card: { backgroundColor: palette.white, borderColor: palette.border, borderWidth: 1, borderRadius: 18, padding: 16, gap: 12 },
  primaryButton: { minHeight: 52, borderRadius: 15, backgroundColor: palette.blue, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 18 },
  primaryButtonText: { color: palette.white, fontSize: 16, fontWeight: '800' },
  disabledButton: { opacity: 0.56 },
  secondaryButton: { minHeight: 48, borderRadius: 15, borderColor: palette.blue, borderWidth: 1.2, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 18, backgroundColor: palette.white },
  secondaryButtonText: { color: palette.blue, fontSize: 15, fontWeight: '800' },
  disabledOutline: { opacity: 0.5 },
  textButton: { minHeight: 42, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 10 },
  textButtonLabel: { color: palette.blue, fontSize: 14, fontWeight: '700' },
  destructiveText: { color: palette.red },
  confirmOverlay: { flex: 1, backgroundColor: 'rgba(23,43,77,0.42)', alignItems: 'center', justifyContent: 'center', padding: 24 },
  confirmDialog: { width: '100%', maxWidth: 420, borderRadius: 20, padding: 22, gap: 12, backgroundColor: palette.white },
  confirmTitle: { color: palette.ink, fontSize: 19, fontWeight: '800' },
  confirmMessage: { color: palette.muted, fontSize: 15, lineHeight: 22 },
  confirmActions: { flexDirection: 'row', gap: 10, marginTop: 6 },
  confirmAction: { flex: 1, minHeight: 48, borderRadius: 14, backgroundColor: palette.blue, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 14 },
  confirmActionDestructive: { backgroundColor: palette.red },
  confirmActionText: { color: palette.white, fontSize: 15, fontWeight: '800' },
  disabledText: { color: palette.muted },
  fieldWrap: { gap: 7 },
  fieldLabel: { color: palette.ink, fontSize: 13, fontWeight: '700' },
  field: { borderWidth: 1, borderColor: palette.border, borderRadius: 13, minHeight: 48, paddingHorizontal: 13, color: palette.ink, backgroundColor: palette.white, fontSize: 15 },
  multilineField: { minHeight: 84, paddingTop: 12, textAlignVertical: 'top' },
  notice: { padding: 13, borderRadius: 13, borderWidth: 1 },
  noticeInfo: { backgroundColor: palette.paleBlue, borderColor: '#D4E5FF' },
  noticeSuccess: { backgroundColor: palette.paleGreen, borderColor: '#BFE7D2' },
  noticeWarning: { backgroundColor: palette.paleAmber, borderColor: '#F2DEAB' },
  noticeError: { backgroundColor: palette.paleRed, borderColor: '#F4C7C3' },
  noticeText: { color: palette.ink, fontSize: 14, lineHeight: 20 },
  sectionTitle: { color: palette.ink, fontSize: 16, fontWeight: '800', marginBottom: 2 },
  choice: { minHeight: 56, padding: 13, borderRadius: 14, borderWidth: 1, borderColor: palette.border, backgroundColor: palette.white, flexDirection: 'row', alignItems: 'center', gap: 12 },
  choiceSelected: { borderColor: palette.blue, backgroundColor: palette.paleBlue },
  choiceCopy: { flex: 1, gap: 3 },
  choiceTitle: { color: palette.ink, fontSize: 15, fontWeight: '700' },
  choiceDetail: { color: palette.muted, fontSize: 13, lineHeight: 18 },
  choiceMark: { width: 22, height: 22, borderWidth: 1, borderColor: '#ABB9CA', borderRadius: 11, alignItems: 'center', justifyContent: 'center' },
  choiceMarkSelected: { borderColor: palette.blue, backgroundColor: palette.blue },
  choiceCheck: { color: palette.white, fontSize: 13, fontWeight: '900' },
});
