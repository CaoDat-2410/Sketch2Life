import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { ParentAuthScreen } from "../features/auth/ParentAuthScreen";
import { ParentWorkflowScreen } from "../features/parent/ParentWorkflowScreen";
import type { AuthenticatedUser } from "../infrastructure/auth/AuthSessionPort";
import { firebasePublicConfig } from "../infrastructure/auth/firebasePublicConfig";
import { FirebaseAuthSession } from "../infrastructure/auth/firebaseAuthSession";

const authSession = new FirebaseAuthSession(firebasePublicConfig);

/** Firebase sign-in gate around the authenticated Parent workflow. */
export function AppRoot(): React.JSX.Element {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [securityOpen, setSecurityOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [securityMessage, setSecurityMessage] = useState("");
  const [securityBusy, setSecurityBusy] = useState(false);

  useEffect(() => {
    let mounted = true;
    authSession.currentUser().then((currentUser) => {
      if (mounted) {
        setUser(currentUser);
        setLoading(false);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator color="#C9794B" />
        <Text style={styles.loadingText}>Đang tải phiên đăng nhập…</Text>
      </View>
    );
  }

  if (!user) {
    return (
      <ParentAuthScreen
        onSignIn={async (email, password) => {
          const authenticated = await authSession.signIn(email, password);
          setUser(authenticated);
          return authenticated;
        }}
        onSignUp={async (email, password) => {
          const authenticated = await authSession.signUp(email, password);
          setUser(authenticated);
          return authenticated;
        }}
        onResetPassword={(email) => authSession.resetPassword(email)}
      />
    );
  }

  return (
    <View style={styles.authenticatedRoot}>
      <View style={styles.accountBar}>
        <Text numberOfLines={1} style={styles.accountLabel}>
          {user.displayName ?? user.email ?? user.subject}
        </Text>
        <Pressable
          accessibilityRole="button"
          onPress={() => { setSecurityMessage(""); setSecurityOpen(true); }}
          style={styles.signOutButton}
        >
          <Text style={styles.signOutText}>Đổi mật khẩu</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          onPress={() => {
            void authSession.signOut().then(() => setUser(null));
          }}
          style={styles.signOutButton}
        >
          <Text style={styles.signOutText}>Đăng xuất</Text>
        </Pressable>
      </View>
      <Modal
        visible={securityOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setSecurityOpen(false)}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.securityCard}>
            <Text style={styles.securityTitle}>Đổi mật khẩu</Text>
            <TextInput
              accessibilityLabel="Mật khẩu hiện tại"
              placeholder="Mật khẩu hiện tại"
              secureTextEntry
              value={currentPassword}
              onChangeText={setCurrentPassword}
              style={styles.securityInput}
            />
            <TextInput
              accessibilityLabel="Mật khẩu mới"
              placeholder="Mật khẩu mới (ít nhất 6 ký tự)"
              secureTextEntry
              value={newPassword}
              onChangeText={setNewPassword}
              style={styles.securityInput}
            />
            <TextInput
              accessibilityLabel="Xác nhận mật khẩu mới"
              placeholder="Nhập lại mật khẩu mới"
              secureTextEntry
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              style={styles.securityInput}
            />
            {securityMessage ? <Text accessibilityRole="alert" style={styles.securityMessage}>{securityMessage}</Text> : null}
            <Pressable
              accessibilityRole="button"
              disabled={securityBusy}
              style={styles.securityPrimary}
              onPress={() => {
                if (newPassword.length < 6 || newPassword !== confirmPassword) {
                  setSecurityMessage("Mật khẩu mới cần đủ 6 ký tự và hai ô phải khớp nhau.");
                  return;
                }
                setSecurityBusy(true);
                setSecurityMessage("");
                void authSession.changePassword(currentPassword, newPassword)
                  .then(() => { setSecurityMessage("Đã đổi mật khẩu."); setCurrentPassword(""); setNewPassword(""); setConfirmPassword(""); })
                  .catch((error: unknown) => setSecurityMessage(error instanceof Error ? error.message : "Không thể đổi mật khẩu."))
                  .finally(() => setSecurityBusy(false));
              }}
            >
              <Text style={styles.securityPrimaryText}>{securityBusy ? "Đang lưu…" : "Cập nhật mật khẩu"}</Text>
            </Pressable>
            <Pressable accessibilityRole="button" onPress={() => setSecurityOpen(false)} style={styles.securityCancel}>
              <Text style={styles.securityCancelText}>Đóng</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
      <ParentWorkflowScreen auth={authSession} />
    </View>
  );
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    backgroundColor: "#F7F3EB",
  },
  loadingText: { color: "#6E685F", fontSize: 13 },
  authenticatedRoot: { flex: 1, backgroundColor: "#F7F3EB" },
  accountBar: {
    minHeight: 48,
    paddingHorizontal: 18,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  accountLabel: { color: "#6E685F", fontSize: 12, flex: 1, marginRight: 12 },
  signOutButton: {
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#D7C8B6",
  },
  signOutText: { color: "#A55E37", fontSize: 12, fontWeight: "700" },
  modalBackdrop: { flex: 1, justifyContent: "center", padding: 22, backgroundColor: "rgba(20, 24, 29, 0.48)" },
  securityCard: { borderRadius: 18, padding: 20, gap: 12, backgroundColor: "#FFFDF9" },
  securityTitle: { color: "#342C24", fontSize: 20, fontWeight: "700" },
  securityInput: { borderWidth: 1, borderColor: "#D7C8B6", borderRadius: 10, padding: 12, color: "#342C24" },
  securityMessage: { color: "#875750", fontSize: 13 },
  securityPrimary: { backgroundColor: "#A55E37", borderRadius: 10, alignItems: "center", padding: 12 },
  securityPrimaryText: { color: "#FFFDF9", fontWeight: "700" },
  securityCancel: { alignItems: "center", padding: 8 },
  securityCancelText: { color: "#6E685F", fontWeight: "600" },
});
