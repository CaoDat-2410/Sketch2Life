import React from 'react';
import { Text } from 'react-native';
import type { StoryRun } from '../../domain/types';
import { Card, ConfirmButton, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  runs: StoryRun[];
  loading: boolean;
  error: string;
  hasMore: boolean;
  onLoad: () => void;
  onLoadMore: () => void;
  onCancel: (runId: string) => void;
  onDelete: (runId: string) => void;
  onBack: () => void;
};

const TERMINAL_STATES = new Set(['COMPLETED', 'FAILED', 'ABANDONED', 'DELETE_PENDING', 'DELETED']);

export function StoryHistoryScreen(props: Props): React.JSX.Element {
  return (
    <ScreenFrame title="Lịch sử hoạt động" subtitle="Các buổi đã lưu trong tài khoản." onBack={props.onBack}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {!props.runs.length && !props.loading ? (
        <Card><SectionTitle>Chưa có buổi nào</SectionTitle><Text style={{ color: palette.muted }}>Các buổi đã bắt đầu sẽ xuất hiện ở đây.</Text><PrimaryButton label="Tải lại" onPress={props.onLoad} /></Card>
      ) : null}
      {props.runs.map((run) => {
        const canCancel = !TERMINAL_STATES.has(run.run_state);
        const canDelete = run.run_state === 'COMPLETED';
        const storyTitle = typeof run.story === 'object' && run.story !== null && 'title' in run.story
          ? String((run.story as { title: unknown }).title)
          : run.context_snapshot.topic || 'Buổi khám phá';
        return (
          <Card key={run.run_id}>
            <SectionTitle>{storyTitle}</SectionTitle>
            <Text style={{ color: palette.muted, fontSize: 13 }}>Trạng thái: {runStateLabel(run.run_state)}</Text>
            <Text style={{ color: palette.muted, fontSize: 13 }}>Chủ đề: {run.context_snapshot.topic || 'Chưa đặt tên'}</Text>
            {canCancel ? <ConfirmButton
              label="Hủy buổi đang mở"
              title="Hủy buổi học?"
              message="Buổi sẽ chuyển sang chờ xóa. Tác vụ và dữ liệu liên quan có thể chưa được dọn cho đến khi worker lifecycle được nối."
              confirmLabel="Hủy buổi"
              destructive
              onConfirm={() => props.onCancel(run.run_id)}
            /> : null}
            {canDelete ? <ConfirmButton
              label="Yêu cầu xóa buổi"
              title="Yêu cầu xóa dữ liệu buổi này?"
              message="Yêu cầu được ghi nhận; trạng thái dọn dữ liệu sẽ được hiển thị từ backend."
              confirmLabel="Yêu cầu xóa"
              destructive
              onConfirm={() => props.onDelete(run.run_id)}
            /> : null}
          </Card>
        );
      })}
      {props.loading ? <Notice text="Đang tải…" /> : null}
      {props.hasMore ? <PrimaryButton label="Xem thêm" busy={props.loading} onPress={props.onLoadMore} /> : null}
    </ScreenFrame>
  );
}

function runStateLabel(value: string): string {
  const labels: Record<string, string> = {
    INPUT_PROCESSING: 'Đang xử lý ảnh',
    SUBJECT_REVIEW: 'Chờ xác nhận chủ thể',
    PREPARATION_REVIEW: 'Đang chuẩn bị nội dung',
    SCRIPT_GENERATING: 'Đang tạo kịch bản',
    SCRIPT_GENERATION_UNKNOWN: 'Đang xác minh kết quả',
    SCRIPT_REVIEW: 'Chờ người lớn xem kịch bản',
    VIDEO_ADMISSION_PENDING: 'Đang chờ xử lý',
    DELETE_PENDING: 'Đang chờ dọn dữ liệu',
    FAILED: 'Không hoàn tất',
    COMPLETED: 'Đã hoàn tất',
    ABANDONED: 'Đã đóng',
    DELETED: 'Đã xóa',
  };
  return labels[value] ?? value;
}
