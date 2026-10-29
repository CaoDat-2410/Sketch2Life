import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, shadows } from '../theme';
import { useAppContext } from '../context/AppContext';
import type { ScreenId } from '../types';

type ParentPlaceholderId =
  | 'sketch_guide'
  | 'transcript_review'
  | 'activity_context_review'
  | 'storyboard'
  | 'script_confirm'
  | 'video_processing'
  | 'safety_gate'
  | 'playback'
  | 'completion';

interface ParentPlaceholderProps {
  screen: ParentPlaceholderId;
  onNavigate?: (screen: ScreenId) => void;
}

const STEP_COPY: Record<ParentPlaceholderId, {
  eyebrow: string;
  title: string;
  description: string;
  next: ParentPlaceholderId | 'capture' | 'ai_processing' | 'scene_understanding' | 'profile';
  action: string;
}> = {
  sketch_guide: {
    eyebrow: 'Tuỳ chọn · AI Sketch Guide',
    title: 'Hướng dẫn vẽ nhanh',
    description: 'AI có thể gợi ý 3–5 bước vẽ chung theo chủ đề và độ khó. Không phân tích trẻ và không bắt buộc phải dùng.',
    next: 'capture',
    action: 'Bỏ qua, đến bước tranh vẽ',
  },
  transcript_review: {
    eyebrow: 'Bước 4 · Transcript review',
    title: 'Kiểm tra lời kể của bé',
    description: 'Bản chép lời sẽ được hiển thị để phụ huynh sửa hoặc xác nhận trước khi AI hiểu tranh.',
    next: 'ai_processing',
    action: 'Xác nhận lời kể',
  },
  activity_context_review: {
    eyebrow: 'Bước 7 · Activity context',
    title: 'Duyệt hoạt động và ngữ cảnh hồ sơ',
    description: 'Phụ huynh xem hoạt động được đề xuất cùng độ tuổi, sở thích và điều kiện an toàn của hồ sơ trẻ.',
    next: 'storyboard',
    action: 'Duyệt hoạt động, tạo storyboard',
  },
  storyboard: {
    eyebrow: 'Bước 8 · Storyboard',
    title: 'Storyboard câu chuyện',
    description: 'Khung này sẽ hiển thị 5–15 cảnh, cho phép xem lại nội dung và thứ tự cảnh trước khi tạo script.',
    next: 'script_confirm',
    action: 'Xác nhận storyboard',
  },
  script_confirm: {
    eyebrow: 'Bước 9 · Script confirmation',
    title: 'Xác nhận kịch bản',
    description: 'Phụ huynh kiểm tra lời dẫn, cảnh và các thông tin an toàn trước khi gửi job tạo video.',
    next: 'video_processing',
    action: 'Gửi yêu cầu tạo video',
  },
  video_processing: {
    eyebrow: 'Bước 10 · Async video job',
    title: 'Đang tạo video',
    description: 'Video được xử lý bất đồng bộ. Người dùng có thể rời màn hình và quay lại từ thông báo khi job hoàn tất.',
    next: 'safety_gate',
    action: 'Mô phỏng job đã hoàn tất',
  },
  safety_gate: {
    eyebrow: 'Bước 11 · Safety gate',
    title: 'Kiểm tra an toàn hoàn tất',
    description: 'Chỉ video đã qua safety gate mới được cấp playback token. Đây không phải bước duyệt video cuối của giáo viên.',
    next: 'playback',
    action: 'Mở playback',
  },
  playback: {
    eyebrow: 'Bước 12 · Playback',
    title: 'Xem video câu chuyện',
    description: 'Màn hình playback sẽ dùng token ngắn hạn và hỗ trợ xem lại hoặc kết thúc phiên.',
    next: 'completion',
    action: 'Hoàn tất phiên',
  },
  completion: {
    eyebrow: 'Hoàn tất',
    title: 'Phiên đã hoàn tất',
    description: 'Tại đây sẽ có trạng thái hoàn tất, huỷ, xoá run và liên kết tới lịch sử hoặc thông báo.',
    next: 'profile',
    action: 'Bắt đầu phiên mới',
  },
};

export const ParentPlaceholderScreen: React.FC<ParentPlaceholderProps> = ({ screen, onNavigate }) => {
  const { navigate, goBack, selectedChild } = useAppContext();
  const nav = onNavigate || navigate;
  const copy = STEP_COPY[screen];

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <TouchableOpacity accessibilityRole="button" accessibilityLabel="Quay lại" onPress={goBack} style={styles.backButton}>
          <Ionicons name="arrow-back" size={19} color={colors.textBody} />
        </TouchableOpacity>
        <Text style={styles.headerLabel}>Parent · SRS V2.2</Text>
        <View style={styles.headerSpacer} />
      </View>

      <View style={styles.stepBadge}>
        <Ionicons name="sparkles-outline" size={16} color="#2563EB" />
        <Text style={styles.stepBadgeText}>{copy.eyebrow}</Text>
      </View>
      <Text style={styles.title}>{copy.title}</Text>
      <Text style={styles.description}>{copy.description}</Text>

      <View style={styles.placeholderCard}>
        <View style={styles.iconCircle}>
          <Ionicons name={screen === 'video_processing' ? 'cloud-upload-outline' : 'construct-outline'} size={28} color="#2563EB" />
        </View>
        <Text style={styles.cardTitle}>Khung chức năng đã sẵn sàng</Text>
        <Text style={styles.cardBody}>
          {selectedChild?.name ? `Hồ sơ đang chọn: ${selectedChild.name}. ` : ''}
          UI chi tiết và API của bước này sẽ được thay thế từng phần trong các lượt tiếp theo.
        </Text>
      </View>

      <TouchableOpacity accessibilityRole="button" onPress={() => nav(copy.next)} style={styles.primaryButton}>
        <Text style={styles.primaryButtonText}>{copy.action}</Text>
        <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
      </TouchableOpacity>
      <Text style={styles.scopeNote}>Chỉ là khung flow — chưa tạo job/API thật ở bước này.</Text>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { padding: 18, paddingBottom: 30, flexGrow: 1 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 22 },
  backButton: { width: 42, height: 42, borderRadius: 21, backgroundColor: '#F1F5F9', alignItems: 'center', justifyContent: 'center' },
  headerLabel: { fontSize: 12, fontWeight: '800', color: colors.textSoft },
  headerSpacer: { width: 42 },
  stepBadge: { flexDirection: 'row', alignItems: 'center', gap: 7, alignSelf: 'flex-start', backgroundColor: '#EFF6FF', borderRadius: 18, paddingHorizontal: 11, paddingVertical: 7 },
  stepBadgeText: { fontSize: 11, fontWeight: '800', color: '#1D4ED8' },
  title: { fontSize: 25, lineHeight: 31, fontWeight: '900', color: colors.textHeading, marginTop: 18 },
  description: { fontSize: 13, lineHeight: 20, color: colors.textSoft, marginTop: 9 },
  placeholderCard: { marginTop: 24, borderRadius: 22, borderWidth: 1, borderColor: '#DBEAFE', backgroundColor: '#F8FBFF', padding: 22, alignItems: 'center', ...shadows.card },
  iconCircle: { width: 64, height: 64, borderRadius: 32, backgroundColor: '#DBEAFE', alignItems: 'center', justifyContent: 'center', marginBottom: 14 },
  cardTitle: { fontSize: 16, fontWeight: '900', color: colors.textHeading, textAlign: 'center' },
  cardBody: { fontSize: 12, lineHeight: 18, color: colors.textSoft, textAlign: 'center', marginTop: 8 },
  primaryButton: { minHeight: 52, marginTop: 22, borderRadius: 17, backgroundColor: '#2563EB', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, paddingHorizontal: 16 },
  primaryButtonText: { color: '#FFFFFF', fontSize: 14, fontWeight: '900' },
  scopeNote: { textAlign: 'center', fontSize: 11, color: colors.textLight, marginTop: 12 },
});
