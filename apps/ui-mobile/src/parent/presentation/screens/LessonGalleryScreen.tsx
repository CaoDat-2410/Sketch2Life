import React from 'react';
import { Text, View } from 'react-native';
import type { LessonDetail, LessonInvitation, LessonSummary, ParentGroupInvitation } from '../../domain/types';
import { Card, ChoiceRow, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, TextButton, palette } from '../components/ui';

type Props = {
  lessons: LessonSummary[];
  selectedLesson: LessonDetail | null;
  selectedPresetVersionId: string | null;
  lessonInvitations: LessonInvitation[];
  groupInvitations: ParentGroupInvitation[];
  loading: boolean;
  loadingId: string;
  error: string;
  onOpenLesson: (lessonId: string) => void;
  onUseLesson: (lesson: LessonDetail) => void;
  onAcceptLessonInvitation: (invitationId: string) => void;
  onDeclineLessonInvitation: (invitationId: string) => void;
  onAcceptGroupInvitation: (membershipId: string) => void;
  onBack: () => void;
  mode?: 'gallery' | 'picker';
};

export function LessonGalleryScreen(props: Props): React.JSX.Element {
  const isPicker = props.mode === 'picker';
  return (
    <ScreenFrame
      title={isPicker ? 'Chọn bài giảng' : 'Thư viện bài giảng'}
      subtitle={isPicker ? 'Đây là tùy chọn. Có thể tiếp tục không cần bài giảng.' : 'Bài giảng được chia sẻ hoặc công khai cho phụ huynh.'}
      step={isPicker ? 'Tùy chọn' : undefined}
      onBack={props.onBack}
    >
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {props.loading ? <Card><Text style={{ color: palette.muted }}>Đang tải thư viện…</Text></Card> : null}
      {props.selectedLesson ? (
        <Card>
          <SectionTitle>{props.selectedLesson.title}</SectionTitle>
          <Text style={{ color: palette.muted, fontSize: 14 }}>{props.selectedLesson.topic} · phiên bản {props.selectedLesson.version_no}</Text>
          <Text style={{ color: palette.ink, fontSize: 14, lineHeight: 20 }}>{props.selectedLesson.drawing_steps_text}</Text>
          <Text style={{ color: palette.ink, fontSize: 14, lineHeight: 20 }}>{props.selectedLesson.subject_learning_notes}</Text>
          {props.selectedLesson.activities.map((activity, index) => (
            <View key={`${activity.title}-${index}`} style={{ gap: 4 }}>
              <Text style={{ color: palette.ink, fontWeight: '700' }}>{activity.title}</Text>
              <Text style={{ color: palette.muted, fontSize: 13, lineHeight: 19 }}>{activity.objective}</Text>
            </View>
          ))}
          <PrimaryButton
            label={props.selectedPresetVersionId === props.selectedLesson.version_id ? 'Đã chọn cho buổi tiếp theo' : 'Dùng bài giảng này'}
            disabled={props.selectedPresetVersionId === props.selectedLesson.version_id}
            onPress={() => props.onUseLesson(props.selectedLesson!)}
          />
        </Card>
      ) : null}
      <Card>
        <SectionTitle>Bài giảng</SectionTitle>
        {props.lessons.length === 0 && !props.loading ? <Text style={{ color: palette.muted }}>Chưa có bài giảng được chia sẻ.</Text> : null}
        {props.lessons.map((lesson) => (
          <ChoiceRow
            key={`${lesson.lesson_id}:${lesson.version_id}`}
            title={lesson.title}
            detail={`${lesson.topic} · ${lesson.activity_count} hoạt động · ${lesson.access_source === 'PUBLIC' ? 'Công khai' : 'Được chia sẻ'}`}
            selected={props.selectedLesson?.lesson_id === lesson.lesson_id}
            onPress={() => props.onOpenLesson(lesson.lesson_id)}
          />
        ))}
        {props.loadingId ? <Text style={{ color: palette.muted, fontSize: 13 }}>Đang tải nội dung…</Text> : null}
      </Card>
      {!isPicker ? <>
        <Card>
          <SectionTitle>Lời mời bài giảng</SectionTitle>
          {props.lessonInvitations.length === 0 ? <Text style={{ color: palette.muted }}>Không có lời mời đang chờ.</Text> : null}
          {props.lessonInvitations.filter((item) => item.state === 'PENDING' || item.state === 'INVITED').map((item) => (
            <View key={item.access_grant_id} style={{ gap: 5, borderTopWidth: 1, borderTopColor: '#E6EDF5', paddingTop: 10 }}>
              <Text style={{ color: palette.ink, fontWeight: '700' }}>Bài giảng được mời chia sẻ</Text>
              <Text style={{ color: palette.muted, fontSize: 12 }}>Hết hạn: {item.expires_at ?? 'không ghi hạn'}</Text>
              <PrimaryButton label="Chấp nhận" onPress={() => props.onAcceptLessonInvitation(item.access_grant_id)} />
              <TextButton label="Từ chối lời mời" onPress={() => props.onDeclineLessonInvitation(item.access_grant_id)} />
            </View>
          ))}
        </Card>
        <Card>
          <SectionTitle>Lời mời nhóm phụ huynh</SectionTitle>
          {props.groupInvitations.length === 0 ? <Text style={{ color: palette.muted }}>Không có lời mời đang chờ.</Text> : null}
          {props.groupInvitations.filter((item) => item.state === 'INVITED').map((item) => (
            <View key={item.membership_id} style={{ gap: 5 }}>
              <Text style={{ color: palette.ink }}>Nhóm phụ huynh · {item.membership_id}</Text>
              <SecondaryButton label="Chấp nhận lời mời" onPress={() => props.onAcceptGroupInvitation(item.membership_id)} />
            </View>
          ))}
        </Card>
      </> : <SecondaryButton label="Tiếp tục không dùng bài giảng" onPress={props.onBack} />}
    </ScreenFrame>
  );
}
