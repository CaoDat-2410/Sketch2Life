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

interface ScreenProps {
  onNavigate?: (screen: ScreenId) => void;
}


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