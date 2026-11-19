import React from 'react';
import { StyleSheet, Text } from 'react-native';
import type { ParentCapabilityState } from '../../application/ports/ParentCapabilityPorts';
import type { StoryRun } from '../../domain/types';
import { Card, ConfirmButton, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  capability: ParentCapabilityState;
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
  if (props.capability.state === 'unavailable') {
    return <ScreenFrame title="Lịch sử buổi học" subtitle="Trạng thái tính năng" onBack={props.onBack}>
      <Notice text="Lịch sử buổi học và các thao tác hủy hoặc xóa chưa khả dụng vì chưa có hợp đồng dịch vụ được xác nhận. Không có thay đổi trạng thái nào được gửi." tone="warning" />
    </ScreenFrame>;
  }

  return (
    <ScreenFrame title="Lịch sử buổi học" subtitle="Các buổi của hồ sơ đang chọn." onBack={props.onBack}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {!props.runs.length && !props.loading ? (
        <Card style={styles.runCard}><SectionTitle>Chưa có buổi nào</SectionTitle><Text style={styles.runDescription}>Các buổi đã bắt đầu sẽ xuất hiện ở đây.</Text><PrimaryButton label="Tải lại" onPress={props.onLoad} /></Card>
      ) : null}
      {props.runs.map((run) => {
        const canCancel = !TERMINAL_STATES.has(run.run_state);
        const canDelete = run.run_state === 'COMPLETED';
        const storyTitle = typeof run.story === 'object' && run.story !== null && 'title' in run.story
          ? String((run.story as { title: unknown }).title)
          : run.context_snapshot.topic || 'Buổi khám phá';
        return (
          <Card key={run.run_id} style={styles.runCard}>
            <Text style={styles.runTitle}>{storyTitle}</Text>
            <Text style={styles.runMeta}>Trạng thái: {runStateLabel(run.run_state)}</Text>
            <Text style={styles.runMeta}>Chủ đề: {run.context_snapshot.topic || 'Chưa đặt tên'}</Text>
            {canCancel ? <ConfirmButton
              label="Hủy buổi đang mở"
              title="Hủy buổi học?"
              message="Buổi sẽ chuyển sang chờ xóa. Tác vụ và dữ liệu liên quan có thể chưa được dọn cho đến khi tiến trình xử lý vòng đời được nối."
              confirmLabel="Hủy buổi"
              destructive
              onConfirm={() => props.onCancel(run.run_id)}
            /> : null}
            {canDelete ? <ConfirmButton
              label="Yêu cầu xóa buổi"
              title="Yêu cầu xóa dữ liệu buổi này?"
              message="Yêu cầu được ghi nhận; trạng thái dọn dữ liệu sẽ được hiển thị từ máy chủ."
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

const styles = StyleSheet.create({
  runCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  runTitle: { color: palette.ink, fontSize: 16, lineHeight: 20, fontWeight: '800', flexShrink: 1, minWidth: 0 },
  runMeta: { color: palette.muted, fontSize: 12, lineHeight: 17, flexShrink: 1, minWidth: 0 },
  runDescription: { color: palette.muted, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
});

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
  return labels[value] ?? 'Trạng thái chưa xác định';
}
