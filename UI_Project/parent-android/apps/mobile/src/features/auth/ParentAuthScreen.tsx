import {useState} from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {ParentButton, ParentCard, ParentField, ParentIcon} from '../../shared/ui/ParentCard';
import {InfoBanner} from '../../shared/ui/FeedbackState';
import {sketchColors, sketchRadius, sketchShadow, sketchSpace} from '../../shared/ui/SketchTokens';

export type ParentAuthMode = 'login' | 'register' | 'recovery';

export function ParentAuthScreen({
  mode,
  onModeChange,
  onEnterPreview,
  onNotice,
}: Readonly<{
  mode: ParentAuthMode;
  onModeChange: (mode: ParentAuthMode) => void;
  onEnterPreview: () => void;
  onNotice: (message: string) => void;
}>): React.JSX.Element {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const title = mode === 'register' ? 'Tạo tài khoản gia đình' : mode === 'recovery' ? 'Lấy lại mật khẩu' : 'Chào mừng ba mẹ';

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.brandRow}>
          <View style={styles.brandMark}><ParentIcon name="spark" size={24} color={sketchColors.white} /></View>
          <View>
            <Text style={styles.brandName}>Sketch2Life</Text>
            <Text style={styles.brandTagline}>Cùng con kể chuyện</Text>
          </View>
        </View>

        <View style={styles.welcomeArt}>
          <View style={styles.artSun} />
          <View style={styles.artHillBack} />
          <View style={styles.artHillFront} />
          <View style={styles.artStoryCard}>
            <Text style={styles.artGlyph}>✦</Text>
            <Text style={styles.artCaption}>Một nét vẽ{ '\n' }mở ra câu chuyện</Text>
          </View>
        </View>

        <View style={styles.formHeading}>
          <Text style={styles.eyebrow}>KHÔNG GIAN GIA ĐÌNH</Text>
          <Text accessibilityRole="header" style={styles.title}>{title}</Text>
          <Text style={styles.subtitle}>
            {mode === 'register'
              ? 'Lưu những câu chuyện nhỏ của con trong một nơi riêng tư.'
              : mode === 'recovery'
                ? 'Nhập email đã đăng ký để bắt đầu khôi phục tài khoản.'
                : 'Biến tranh của con thành những khoảnh khắc kể chuyện.'}
          </Text>
        </View>

        <ParentCard style={styles.formCard}>
          {mode === 'register' ? (
            <ParentField label="Tên ba mẹ" value={displayName} onChangeText={setDisplayName} placeholder="Tên hiển thị" />
          ) : null}
          <ParentField
            autoCapitalize="none"
            keyboardType="email-address"
            label="Email"
            value={email}
            onChangeText={setEmail}
            placeholder="ban@email.com"
          />
          {mode !== 'recovery' ? (
            <ParentField
              label="Mật khẩu"
              value={password}
              onChangeText={setPassword}
              placeholder="Nhập mật khẩu"
              secureTextEntry
              textContentType={mode === 'register' ? 'newPassword' : 'password'}
            />
          ) : null}
          {mode === 'login' ? (
            <Pressable accessibilityRole="button" onPress={() => onModeChange('recovery')} style={styles.forgotLink}>
              <Text style={styles.linkText}>Quên mật khẩu?</Text>
            </Pressable>
          ) : null}
          <ParentButton
            title={mode === 'register' ? 'Tạo tài khoản' : mode === 'recovery' ? 'Gửi hướng dẫn' : 'Đăng nhập'}
            onPress={() => onNotice('Đăng nhập và đăng ký chưa kết nối dịch vụ xác thực trong bản này.')}
          />
          <InfoBanner
            title="Đăng nhập chưa kết nối"
            body="Biểu mẫu chưa gửi thông tin tới máy chủ. Dùng nút trải nghiệm để xem các màn hình mẫu."
          />
        </ParentCard>

        <View style={styles.switchModeRow}>
          {mode === 'register' ? (
            <Text style={styles.switchText}>Đã có tài khoản? </Text>
          ) : mode === 'recovery' ? (
            <Text style={styles.switchText}>Nhớ mật khẩu rồi? </Text>
          ) : (
            <Text style={styles.switchText}>Lần đầu đến đây? </Text>
          )}
          <Pressable onPress={() => onModeChange(mode === 'register' || mode === 'recovery' ? 'login' : 'register')}>
            <Text style={styles.linkText}>{mode === 'register' ? 'Đăng nhập' : mode === 'recovery' ? 'Quay lại' : 'Tạo tài khoản'}</Text>
          </Pressable>
        </View>

        <ParentButton title="Xem bản trải nghiệm" icon="arrow" variant="secondary" onPress={onEnterPreview} />
        <Text style={styles.privacyNote}>Riêng tư từ thiết kế · Ba mẹ kiểm soát hồ sơ và nội dung của con</Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: {flex: 1, backgroundColor: sketchColors.canvas},
  content: {width: '100%', maxWidth: 560, alignSelf: 'center', padding: sketchSpace.xl, paddingBottom: 36, gap: 17},
  brandRow: {flexDirection: 'row', alignItems: 'center', gap: 11, marginBottom: 2},
  brandMark: {width: 44, height: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 15, backgroundColor: sketchColors.green},
  brandName: {color: sketchColors.ink, fontSize: 18, fontWeight: '900', letterSpacing: -0.4},
  brandTagline: {color: sketchColors.muted, fontSize: 10, fontWeight: '600'},
  welcomeArt: {position: 'relative', height: 168, overflow: 'hidden', borderRadius: sketchRadius.lg, backgroundColor: '#EAF3E7'},
  artSun: {position: 'absolute', top: 18, right: 28, width: 53, height: 53, borderRadius: 27, backgroundColor: '#F3D781'},
  artHillBack: {position: 'absolute', right: -24, bottom: -69, width: 245, height: 155, borderRadius: 130, backgroundColor: '#C7DFCA', transform: [{rotate: '-11deg'}]},
  artHillFront: {position: 'absolute', left: -33, bottom: -99, width: 275, height: 176, borderRadius: 150, backgroundColor: '#A6CCB1', transform: [{rotate: '8deg'}]},
  artStoryCard: {position: 'absolute', top: 30, left: 21, width: 176, height: 104, justifyContent: 'center', padding: 15, borderRadius: 18, borderWidth: 1, borderColor: '#FFFFFF', backgroundColor: '#FFFEFA', shadowColor: '#244C38', shadowOpacity: 0.12, shadowRadius: 13, shadowOffset: {width: 0, height: 7}, elevation: 3},
  artGlyph: {color: sketchColors.gold, fontSize: 23, fontWeight: '900'},
  artCaption: {color: sketchColors.ink, fontSize: 13, fontWeight: '800', lineHeight: 18},
  formHeading: {gap: 5, marginTop: 2},
  eyebrow: {color: sketchColors.green, fontSize: 10, fontWeight: '900', letterSpacing: 1.4},
  title: {color: sketchColors.ink, fontSize: 25, lineHeight: 31, fontWeight: '900', letterSpacing: -0.5},
  subtitle: {color: sketchColors.muted, fontSize: 12, lineHeight: 18},
  formCard: {gap: 13, padding: 15},
  forgotLink: {alignSelf: 'flex-end', paddingVertical: 3},
  linkText: {color: sketchColors.greenDark, fontSize: 12, fontWeight: '800'},
  switchModeRow: {flexDirection: 'row', justifyContent: 'center', alignItems: 'center'},
  switchText: {color: sketchColors.muted, fontSize: 12},
  privacyNote: {maxWidth: 330, alignSelf: 'center', color: sketchColors.muted, fontSize: 10, lineHeight: 15, textAlign: 'center'},
});
