import React, { useState, type ReactNode } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

export const authTokens = {
  ink: '#332B2A',
  body: '#6B5F59',
  muted: '#8A7E77',
  plum: '#5B3587',
  plumDark: '#45215F',
  sunGold: '#F4A90B',
  lavender: '#FFF2E8',
  lavenderLine: '#E8D9CC',
  sky: '#DDF5F5',
  mint: '#DDF7EE',
  butter: '#FFF1B8',
  butterInk: '#654D16',
  coral: '#FFB7A5',
  paper: '#FFFCF7',
  white: '#FFFFFF',
  border: '#E8DCCF',
  error: '#A0393B',
  errorFill: '#FDE5E1',
  info: '#245A79',
  infoFill: '#E2F2FF',
  disabled: '#EEE9ED',
  disabledInk: '#6D6570',
} as const;

type IconName = React.ComponentProps<typeof Ionicons>['name'];

export function AuthField({ label, icon, right, error, style, onFocus, onBlur, accessibilityLabel, accessibilityHint, ...props }: TextInputProps & {
  label: string;
  icon: IconName;
  right?: ReactNode;
  error?: string;
}): React.JSX.Element {
  const [focused, setFocused] = useState(false);

  return (
    <View style={styles.fieldGroup}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={[styles.inputShell, focused && styles.inputShellFocused, error && styles.inputShellError]}>
        <Ionicons name={icon} size={20} color={focused ? authTokens.plum : authTokens.muted} accessible={false} />
        <TextInput
          {...props}
          accessibilityLabel={accessibilityLabel ?? label}
          accessibilityHint={error || accessibilityHint}
          onFocus={(event) => {
            setFocused(true);
            onFocus?.(event);
          }}
          onBlur={(event) => {
            setFocused(false);
            onBlur?.(event);
          }}
          placeholderTextColor={authTokens.muted}
          selectionColor={authTokens.plum}
          style={[styles.input, style]}
        />
        {right}
      </View>
      {error ? <Text accessibilityRole="alert" style={styles.fieldError}>{error}</Text> : null}
    </View>
  );
}

export function AuthButton({ label, onPress, disabled = false, busy = false, variant = 'primary', icon }: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  busy?: boolean;
  variant?: 'primary' | 'secondary';
  icon?: IconName;
}): React.JSX.Element {
  const [focused, setFocused] = useState(false);
  const isDisabled = disabled || busy;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: isDisabled, busy }}
      disabled={isDisabled}
      hitSlop={4}
      onPress={onPress}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      android_ripple={{ color: variant === 'primary' ? '#FFFFFF30' : '#5B358720' }}
      style={({ pressed }) => [
        styles.button,
        variant === 'primary' ? styles.primaryButton : styles.secondaryButton,
        isDisabled && styles.buttonDisabled,
        pressed && !isDisabled && styles.buttonPressed,
        focused && styles.focused,
      ]}
    >
      {variant === 'primary' && !isDisabled ? <LinearGradient colors={[authTokens.plum, authTokens.plumDark]} style={StyleSheet.absoluteFillObject} /> : null}
      <View style={styles.buttonContent}>
        {busy ? <ActivityIndicator color={variant === 'primary' ? authTokens.white : authTokens.plum} /> : null}
        {!busy && icon ? <Ionicons name={icon} size={19} color={isDisabled ? authTokens.disabledInk : variant === 'primary' ? authTokens.white : authTokens.plum} accessible={false} /> : null}
        {!busy ? <Text style={[styles.buttonText, variant === 'secondary' && styles.secondaryButtonText, isDisabled && styles.buttonDisabledText]}>{label}</Text> : null}
      </View>
    </Pressable>
  );
}

export function AuthTextButton({ label, onPress, disabled = false }: { label: string; onPress: () => void; disabled?: boolean }): React.JSX.Element {
  const [focused, setFocused] = useState(false);

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled }}
      disabled={disabled}
      hitSlop={8}
      onPress={onPress}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={({ pressed }) => [styles.textButton, pressed && styles.textButtonPressed, focused && styles.textButtonFocused]}
    >
      <Text style={[styles.textButtonLabel, disabled && styles.buttonDisabledText]}>{label}</Text>
    </Pressable>
  );
}

export function AuthNotice({ text, tone = 'info' }: { text: string; tone?: 'info' | 'warning' | 'error' }): React.JSX.Element {
  const isError = tone === 'error';
  const isWarning = tone === 'warning';
  const icon: IconName = isError ? 'alert-circle-outline' : isWarning ? 'warning-outline' : 'information-circle-outline';
  const color = isError ? authTokens.error : isWarning ? authTokens.butterInk : authTokens.info;

  return (
    <View accessible accessibilityRole={isError ? 'alert' : 'summary'} style={[styles.notice, isError ? styles.errorNotice : isWarning ? styles.warningNotice : styles.infoNotice]}>
      <Ionicons name={icon} size={18} color={color} accessible={false} />
      <Text style={[styles.noticeText, { color }]}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  fieldGroup: { gap: 7 },
  fieldLabel: { color: authTokens.ink, fontSize: 13, lineHeight: 18, fontWeight: '800' },
  inputShell: { minHeight: 54, borderWidth: 1.5, borderColor: authTokens.border, borderRadius: 17, paddingHorizontal: 15, flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: authTokens.paper },
  inputShellFocused: { borderColor: authTokens.plum, borderWidth: 2.5, backgroundColor: authTokens.white, shadowColor: authTokens.plum, shadowOpacity: 0.12, shadowRadius: 8, elevation: 2 },
  inputShellError: { borderColor: authTokens.error },
  input: { flex: 1, minWidth: 0, minHeight: 50, paddingHorizontal: 0, paddingVertical: 10, color: authTokens.ink, fontSize: 15, lineHeight: 20 },
  fieldError: { color: authTokens.error, fontSize: 12, lineHeight: 17, fontWeight: '700' },
  button: { minHeight: 54, borderRadius: 18, overflow: 'hidden', justifyContent: 'center', alignItems: 'center', paddingHorizontal: 16 },
  primaryButton: { shadowColor: authTokens.plumDark, shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.2, shadowRadius: 10, elevation: 4 },
  secondaryButton: { borderWidth: 1.5, borderColor: authTokens.lavenderLine, backgroundColor: authTokens.white },
  buttonContent: { minHeight: 52, width: '100%', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 },
  buttonText: { color: authTokens.white, fontSize: 15, lineHeight: 20, fontWeight: '900', textAlign: 'center', flexShrink: 1 },
  secondaryButtonText: { color: authTokens.plumDark },
  buttonDisabled: { backgroundColor: authTokens.disabled, borderColor: authTokens.border, shadowOpacity: 0, elevation: 0 },
  buttonDisabledText: { color: authTokens.disabledInk },
  buttonPressed: { transform: [{ scale: 0.985 }], opacity: 0.94 },
  focused: { borderColor: authTokens.plum, borderWidth: 2.5 },
  textButton: { minHeight: 44, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 8, borderRadius: 12 },
  textButtonLabel: { color: authTokens.plum, fontSize: 14, lineHeight: 19, fontWeight: '900', textAlign: 'center' },
  textButtonPressed: { opacity: 0.7 },
  textButtonFocused: { backgroundColor: authTokens.lavender },
  notice: { minHeight: 48, borderRadius: 15, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 10, flexDirection: 'row', alignItems: 'flex-start', gap: 9 },
  infoNotice: { backgroundColor: authTokens.infoFill, borderColor: '#BBDDF2' },
  warningNotice: { backgroundColor: authTokens.butter, borderColor: '#F0D77E' },
  errorNotice: { backgroundColor: authTokens.errorFill, borderColor: '#F2B9B0' },
  noticeText: { flex: 1, minWidth: 0, fontSize: 12, lineHeight: 17, fontWeight: '600' },
});
