import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Svg, { Path, Circle, Rect, Ellipse } from 'react-native-svg';
import { colors, radius, shadows } from '../theme';
import { Kid3DButton } from '../components/Kid3DButton';
import type { ScreenId } from '../types';
import { useAppContext } from '../context/AppContext';

interface ScreenProps {
  onNavigate?: (screen: ScreenId) => void;
}

// ==========================================
// Cute Vector Mascots for Error States
// ==========================================
const SadMascotSvg: React.FC<{ size?: number }> = ({ size = 120 }) => (
  <Svg width={size} height={size} viewBox="0 0 120 120" fill="none">
    {/* Body */}
    <Ellipse cx={60} cy={65} rx={42} ry={40} fill="#93C5FD" />
    <Ellipse cx={60} cy={65} rx={38} ry={36} fill="#60A5FA" />
    {/* Ears */}
    <Circle cx={32} cy={34} r={12} fill="#3B82F6" />
    <Circle cx={88} cy={34} r={12} fill="#3B82F6" />
    <Circle cx={32} cy={34} r={7} fill="#93C5FD" />
    <Circle cx={88} cy={34} r={7} fill="#93C5FD" />
    {/* Sad Eyes */}
    <Path d="M42 56Q48 50 54 56" stroke="#1E3A8A" strokeWidth={3} strokeLinecap="round" />
    <Path d="M66 56Q72 50 78 56" stroke="#1E3A8A" strokeWidth={3} strokeLinecap="round" />
    {/* Tear Drop */}
    <Path d="M40 68C40 73 36 78 36 78C36 78 32 73 32 68C32 65 34 63 36 63C38 63 40 65 40 68Z" fill="#38BDF8" />
    {/* Sad Mouth */}
    <Path d="M52 76Q60 70 68 76" stroke="#1E3A8A" strokeWidth={3} strokeLinecap="round" />
    {/* Blushing cheeks */}
    <Circle cx={38} cy={68} r={5} fill="#F472B6" opacity={0.6} />
    <Circle cx={82} cy={68} r={5} fill="#F472B6" opacity={0.6} />
  </Svg>
);

const EaselWarningSvg: React.FC<{ size?: number }> = ({ size = 120 }) => (
  <Svg width={size} height={size} viewBox="0 0 120 120" fill="none">
    {/* Easel legs */}
    <Path d="M30 110L55 25M90 110L65 25M60 25V110" stroke="#92400E" strokeWidth={4} strokeLinecap="round" />
    {/* Easel shelf */}
    <Rect x={22} y={75} width={76} height={6} rx={3} fill="#78350F" />
    {/* Canvas Board */}
    <Rect x={30} y={35} width={60} height={42} rx={6} fill="#FEF9C3" stroke="#FDE047" strokeWidth={2} />
    {/* Drawing doodle */}
    <Circle cx={50} cy={52} r={8} fill="#F472B6" />
    <Circle cx={65} cy={54} r={6} fill="#38BDF8" />
    <Path d="M38 68Q48 60 58 68Q68 60 78 68" stroke="#22C55E" strokeWidth={3} strokeLinecap="round" />
    {/* Big Red Exclamation Badge */}
    <Circle cx={84} cy={42} r={14} fill="#EF4444" stroke="#FFFFFF" strokeWidth={2.5} />
    <Path d="M84 35V43" stroke="#FFFFFF" strokeWidth={3} strokeLinecap="round" />
    <Circle cx={84} cy={48} r={1.5} fill="#FFFFFF" />
  </Svg>
);

// ==========================================
// 21. LỖI PIXL — Có phương án dự phòng
// ==========================================
export const PixlErrorScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <View style={styles.screenFull}>
      <View style={styles.header}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Thông báo</Text>
        <View style={{ width: 34 }} />
      </View>

      <View style={styles.centerContent}>
        <View style={{ marginVertical: 16 }}>
          <SadMascotSvg size={130} />
        </View>

        <Text style={styles.errorTitle}>
          Phần chuyển động{'\n'}chưa mở được
        </Text>
        <Text style={styles.errorSubtitle}>
          Bạn vẫn có thể tiếp tục bằng ảnh tĩnh và hướng dẫn hoạt động nhé!
        </Text>
      </View>

      <View style={styles.bottomActions}>
        <Kid3DButton
          title="Tiếp tục bằng ảnh tĩnh →"
          color="blue"
          size="lg"
          onPress={() => nav('child_guide')}
        />
        <TouchableOpacity
          onPress={() => nav('story_preview')}
          style={styles.secondaryLinkBtn}
        >
          <Text style={styles.secondaryLinkText}>Thử lại</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

// ==========================================
// 22. LỖI XỬ LÝ AI
// ==========================================
export const AiErrorScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <ScrollView contentContainerStyle={styles.scrollScreen} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Hỗ trợ xử lý</Text>
        <View style={{ width: 34 }} />
      </View>

      <View style={styles.centerContent}>
        <Image
          source={require('../../assets/images/robot_ai.png')}
          style={{ width: 140, height: 140, resizeMode: 'contain', marginVertical: 12 }}
        />

        <Text style={styles.errorTitle}>
          Hiện tại chưa thể phân tích{'\n'}bức tranh này
        </Text>
      </View>

      {/* Suggestion Checklist matching Image 1 Screen 22 */}
      <View style={styles.tipsCard}>
        <Text style={styles.tipsCardHeader}>Bạn có thể thử:</Text>
        <View style={styles.tipRow}>
          <Ionicons name="sunny-outline" size={16} color="#2563EB" />
          <Text style={styles.tipRowText}>Chụp ảnh rõ hơn, đủ ánh sáng</Text>
        </View>
        <View style={styles.tipRow}>
          <Ionicons name="color-palette-outline" size={16} color="#2563EB" />
          <Text style={styles.tipRowText}>Đảm bảo là bức vẽ của trẻ</Text>
        </View>
        <View style={styles.tipRow}>
          <Ionicons name="shield-checkmark-outline" size={16} color="#2563EB" />
          <Text style={styles.tipRowText}>Không dùng ảnh có khuôn mặt trẻ em</Text>
        </View>
      </View>

      <View style={styles.bottomActions}>
        <Kid3DButton
          title="Thử lại 🔄"
          color="blue"
          size="lg"
          onPress={() => nav('ai_processing')}
        />
        <TouchableOpacity
          onPress={() => nav('capture')}
          style={styles.outlineActionBtn}
        >
          <Text style={styles.outlineActionText}>Chọn ảnh khác</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

// ==========================================
// 23. THIẾU BƯỚC — Chưa chọn chủ đề
// ==========================================
export const MissingStepScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <View style={styles.screenFull}>
      <View style={styles.header}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Nhắc nhở</Text>
        <View style={{ width: 34 }} />
      </View>

      <View style={styles.centerContent}>
        <View style={{ marginVertical: 16 }}>
          <EaselWarningSvg size={130} />
        </View>

        <Text style={styles.errorTitle}>
          Cần xác nhận chủ đề{'\n'}trước khi tiếp tục
        </Text>
        <Text style={styles.errorSubtitle}>
          Vui lòng chọn chủ đề chính từ bức tranh để xem hoạt động gợi ý phù hợp.
        </Text>
      </View>

      <View style={styles.bottomActions}>
        <Kid3DButton
          title="Xem lại chủ đề →"
          color="blue"
          size="lg"
          onPress={() => nav('scene_understanding')}
        />
        <TouchableOpacity
          onPress={() => nav('dashboard')}
          style={styles.secondaryLinkBtn}
        >
          <Text style={styles.secondaryLinkText}>Về trang chủ</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

// ==========================================
// 24. KHÔNG CÓ KẾT QUẢ PHÙ HỢP
// ==========================================
export const NoResultsScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;

  return (
    <ScrollView contentContainerStyle={styles.scrollScreen} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Gợi ý hoạt động</Text>
        <View style={{ width: 34 }} />
      </View>

      <View style={styles.centerContent}>
        <View style={{ marginVertical: 16 }}>
          <SadMascotSvg size={120} />
        </View>

        <Text style={styles.errorTitle}>
          Chưa có hoạt động phù hợp{'\n'}lần này
        </Text>
      </View>

      <View style={styles.tipsCard}>
        <Text style={styles.tipsCardHeader}>Bạn có thể thử:</Text>
        <View style={styles.tipRow}>
          <Ionicons name="refresh-outline" size={16} color="#2563EB" />
          <Text style={styles.tipRowText}>Chọn chủ đề khác</Text>
        </View>
        <View style={styles.tipRow}>
          <Ionicons name="mic-outline" size={16} color="#2563EB" />
          <Text style={styles.tipRowText}>Thêm lời kể của bé</Text>
        </View>
        <View style={styles.tipRow}>
          <Ionicons name="sparkles-outline" size={16} color="#2563EB" />
          <Text style={styles.tipRowText}>Hoặc khám phá các hoạt động phổ biến</Text>
        </View>
      </View>

      <View style={styles.bottomActions}>
        <Kid3DButton
          title="Thử chủ đề khác ✨"
          color="blue"
          size="lg"
          onPress={() => nav('scene_understanding')}
        />
        <TouchableOpacity
          onPress={() => nav('activity_recommend')}
          style={styles.outlineActionBtn}
        >
          <Text style={styles.outlineActionText}>Xem hoạt động phổ biến</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

// ==========================================
// 25. CÀI ĐẶT & QUYỀN RIÊNG TƯ
// ==========================================
export const SettingsScreen: React.FC<ScreenProps> = ({ onNavigate }) => {
  const { navigate, goBack } = useAppContext();
  const nav = onNavigate || navigate;

  const settingSections = [
    { id: 'privacy', title: 'Quyền riêng tư & an toàn', icon: 'shield-checkmark', color: '#16A34A', bg: '#DCFCE7' },
    { id: 'data',    title: 'Dữ liệu của bé',          icon: 'person',           color: '#D97706', bg: '#FEF3C7' },
    { id: 'lang',    title: 'Ngôn ngữ',                icon: 'globe',            color: '#2563EB', bg: '#DBEAFE', extra: 'Tiếng Việt' },
    { id: 'notify',  title: 'Thông báo',               icon: 'notifications',    color: '#0891B2', bg: '#CFFAFE' },
    { id: 'help',    title: 'Trợ giúp',                icon: 'help-circle',      color: '#7C3AED', bg: '#F3E8FF' },
    { id: 'about',   title: 'Về Sketch2Life',          icon: 'sparkles',         color: '#E11D48', bg: '#FFE4E6' },
  ];

  return (
    <ScrollView contentContainerStyle={styles.scrollScreen} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <TouchableOpacity onPress={goBack} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={20} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Cài đặt</Text>
        <View style={{ width: 34 }} />
      </View>

      <View style={{ gap: 10, marginVertical: 14 }}>
        {settingSections.map((item) => (
          <TouchableOpacity
            key={item.id}
            activeOpacity={0.85}
            style={styles.settingRow}
          >
            <View style={[styles.settingIconTile, { backgroundColor: item.bg }]}>
              <Ionicons name={item.icon as any} size={20} color={item.color} />
            </View>
            <Text style={styles.settingRowTitle}>{item.title}</Text>
            {item.extra && (
              <Text style={styles.settingRowExtra}>{item.extra}</Text>
            )}
            <Ionicons name="chevron-forward" size={18} color="#94A3B8" />
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.appVersionBox}>
        <Text style={styles.appVersionText}>Sketch2Life v1.2.0 (Montessori Edition)</Text>
      </View>
    </ScrollView>
  );
};

// ===================== STYLES =====================
const styles = StyleSheet.create({
  screenFull: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: 18,
    justifyContent: 'space-between',
  },
  scrollScreen: {
    padding: 18,
    paddingBottom: 28,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  backBtn: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '900',
    color: colors.textHeading,
  },
  centerContent: {
    alignItems: 'center',
    gap: 8,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '900',
    color: colors.textHeading,
    textAlign: 'center',
    lineHeight: 26,
  },
  errorSubtitle: {
    fontSize: 12,
    color: colors.textSoft,
    textAlign: 'center',
    lineHeight: 18,
    paddingHorizontal: 16,
    maxWidth: 300,
  },
  tipsCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 14,
    gap: 10,
    marginVertical: 14,
    ...shadows.card,
  },
  tipsCardHeader: {
    fontSize: 12.5,
    fontWeight: '800',
    color: colors.textHeading,
  },
  tipRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  tipRowText: {
    fontSize: 11.5,
    color: colors.textBody,
  },
  bottomActions: {
    marginTop: 18,
    marginBottom: 8,
    gap: 8,
  },
  secondaryLinkBtn: {
    alignItems: 'center',
    paddingVertical: 10,
  },
  secondaryLinkText: {
    fontSize: 12.5,
    fontWeight: '700',
    color: colors.textSoft,
  },
  outlineActionBtn: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
  },
  outlineActionText: {
    fontSize: 12.5,
    fontWeight: '800',
    color: colors.textHeading,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 14,
    gap: 12,
    ...shadows.card,
  },
  settingIconTile: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  settingRowTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: colors.textHeading,
    flex: 1,
  },
  settingRowExtra: {
    fontSize: 11.5,
    color: colors.textSoft,
    fontWeight: '600',
  },
  appVersionBox: {
    alignItems: 'center',
    marginTop: 20,
  },
  appVersionText: {
    fontSize: 11,
    color: colors.textLight,
  },
});
