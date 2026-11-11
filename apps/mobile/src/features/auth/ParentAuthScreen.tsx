import React, { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import type { AuthenticatedUser } from "../../infrastructure/auth/AuthSessionPort";

type AuthMode = "sign-in" | "sign-up" | "reset";

type Props = Readonly<{
  onSignIn: (email: string, password: string) => Promise<AuthenticatedUser>;
  onSignUp: (email: string, password: string) => Promise<AuthenticatedUser>;
  onResetPassword: (email: string) => Promise<void>;
}>;

export function ParentAuthScreen({
  onSignIn,
  onSignUp,
  onResetPassword,
}: Props): React.JSX.Element {
  const [mode, setMode] = useState<AuthMode>("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const submit = async () => {
    setError(null);
    setNotice(null);
    if (!email.trim() || !email.includes("@")) {
      setError("Nhập địa chỉ email hợp lệ.");
      return;
    }
    if (mode !== "reset" && password.length < 6) {
      setError("Mật khẩu cần có ít nhất 6 ký tự.");
      return;
    }

    setBusy(true);
    try {
      if (mode === "reset") {
        await onResetPassword(email);
        setNotice("Nếu email đã đăng ký, hướng dẫn đặt lại mật khẩu sẽ được gửi.");
      } else if (mode === "sign-up") {
        await onSignUp(email, password);
      } else {
        await onSignIn(email, password);
      }
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Có lỗi xác thực. Vui lòng thử lại.",
      );
    } finally {
      setBusy(false);
    }
  };

  const isSignUp = mode === "sign-up";
  const isReset = mode === "reset";
  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.flex}
      >
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.mark} accessibilityLabel="Sketch2Life">
            <Text style={styles.markText}>s</Text>
          </View>
          <Text style={styles.eyebrow}>SKETCH2LIFE · PHỤ HUYNH</Text>
          <Text style={styles.title}>
            {isReset ? "Đặt lại mật khẩu" : isSignUp ? "Tạo tài khoản" : "Chào mừng trở lại"}
          </Text>
          <Text style={styles.subtitle}>
            {isReset
              ? "Nhập email để nhận hướng dẫn đặt lại mật khẩu."
              : isSignUp
              ? "Tạo tài khoản xác thực để bắt đầu."
              : "Đăng nhập để tiếp tục với Sketch2Life."}
          </Text>

          <View style={styles.form}>
            <Text style={styles.label}>Email</Text>
            <TextInput
              accessibilityLabel="Email"
              autoCapitalize="none"
              autoComplete="email"
              autoCorrect={false}
              keyboardType="email-address"
              onChangeText={setEmail}
              placeholder="ban@example.com"
              placeholderTextColor="#9C9489"
              returnKeyType="next"
              textContentType="emailAddress"
              value={email}
              style={styles.input}
            />

            {!isReset && (
              <>
                <Text style={styles.label}>Mật khẩu</Text>
                <TextInput
                  accessibilityLabel="Mật khẩu"
                  autoCapitalize="none"
                  autoComplete={isSignUp ? "new-password" : "current-password"}
                  onChangeText={setPassword}
                  placeholder="Ít nhất 6 ký tự"
                  placeholderTextColor="#9C9489"
                  secureTextEntry
                  textContentType={isSignUp ? "newPassword" : "password"}
                  value={password}
                  style={styles.input}
                />
              </>
            )}

            {notice !== null && (
              <View accessibilityLiveRegion="polite" style={styles.noticeBox}>
                <Text style={styles.noticeText}>{notice}</Text>
              </View>
            )}
            {error !== null && (
              <View accessibilityRole="alert" style={styles.errorBox}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}

            <Pressable
              accessibilityRole="button"
              disabled={busy}
              onPress={submit}
              style={[styles.primaryButton, busy && styles.disabledButton]}
            >
              {busy ? (
                <ActivityIndicator color="#FFFDF9" />
              ) : (
                <Text style={styles.primaryButtonText}>
                  {isReset ? "Gửi hướng dẫn" : isSignUp ? "Tạo tài khoản" : "Đăng nhập"}
                </Text>
              )}
            </Pressable>

            {isReset ? (
              <Pressable
                accessibilityRole="button"
                disabled={busy}
                onPress={() => { setError(null); setNotice(null); setMode("sign-in"); }}
                style={styles.modeButton}
              >
                <Text style={styles.modeText}>Quay lại đăng nhập</Text>
              </Pressable>
            ) : (
              <>
                {!isSignUp && (
                  <Pressable
                    accessibilityRole="button"
                    disabled={busy}
                    onPress={() => { setError(null); setNotice(null); setMode("reset"); }}
                    style={styles.modeButton}
                  >
                    <Text style={styles.modeText}>Quên mật khẩu?</Text>
                  </Pressable>
                )}
                <Pressable
                  accessibilityRole="button"
                  disabled={busy}
                  onPress={() => {
                    setError(null);
                    setNotice(null);
                    setMode(isSignUp ? "sign-in" : "sign-up");
                  }}
                  style={styles.modeButton}
                >
                  <Text style={styles.modeText}>
                    {isSignUp ? "Đã có tài khoản? Đăng nhập" : "Chưa có tài khoản? Tạo tài khoản"}
                  </Text>
                </Pressable>
              </>
            )}
          </View>

          <Text style={styles.footnote}>
            Tài khoản đăng ký ở đây được hệ thống cấp vai trò phụ huynh. Hồ sơ trẻ
            được thiết lập riêng sau khi đăng nhập.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F7F3EB" },
  flex: { flex: 1 },
  container: { flexGrow: 1, justifyContent: "center", padding: 26, gap: 10 },
  mark: {
    width: 54,
    height: 54,
    borderRadius: 18,
    backgroundColor: "#C9794B",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  markText: { color: "#FFFDF9", fontSize: 32, fontWeight: "800" },
  eyebrow: {
    color: "#A56538",
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 1.4,
  },
  title: { color: "#25231F", fontSize: 31, lineHeight: 38, fontWeight: "800" },
  subtitle: {
    color: "#6E685F",
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 16,
  },
  form: {
    backgroundColor: "#FFFDF9",
    borderRadius: 22,
    borderWidth: 1,
    borderColor: "#E9E0D3",
    padding: 18,
    gap: 10,
  },
  label: { color: "#4D473F", fontSize: 12, fontWeight: "800", marginTop: 4 },
  input: {
    minHeight: 50,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E0D3C2",
    paddingHorizontal: 14,
    color: "#25231F",
    fontSize: 15,
    backgroundColor: "#FFFEFC",
  },
  errorBox: { backgroundColor: "#FDE9E5", borderRadius: 12, padding: 12 },
  errorText: { color: "#875750", fontSize: 13, lineHeight: 18 },
  noticeBox: { backgroundColor: "#ECF8F0", borderColor: "#B9DDC9", borderWidth: 1, borderRadius: 12, padding: 12 },
  noticeText: { color: "#286143", fontSize: 13, lineHeight: 18 },
  primaryButton: {
    minHeight: 50,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#C9794B",
    marginTop: 7,
  },
  disabledButton: { opacity: 0.65 },
  primaryButtonText: { color: "#FFFDF9", fontSize: 15, fontWeight: "800" },
  modeButton: { alignItems: "center", paddingVertical: 9 },
  modeText: { color: "#A55E37", fontSize: 13, fontWeight: "700" },
  footnote: { color: "#8A8278", fontSize: 11, lineHeight: 17, marginTop: 11 },
});
