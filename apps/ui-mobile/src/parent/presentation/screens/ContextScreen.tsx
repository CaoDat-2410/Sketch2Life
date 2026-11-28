import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import type { ParentContextEntryKind, ParentContextEntryListView, ParentProfileViewV1, ParentStoryRunV1 } from '../../domain/types';
import { isParentRunContextSnapshotV2 } from '../../domain/types';
import { safeParentFlowErrorMessage } from '../navigation/parentFlowV1';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, SecondaryButton, palette } from '../components/ui';
import { isConfirmedRunSubject } from '../navigation/parentFlowV1';

type Props = {
  profile: ParentProfileViewV1 | null;
  contextRun: ParentStoryRunV1 | null;
  stepLabel: string;
  busy: boolean;
  confirmed: boolean;
  error: string;
  onRetryCreate: () => void;
  onConfirm: (selectedContextEntryIds?: readonly string[]) => Promise<'confirmed' | 'entry-not-found' | 'already-confirmed' | 'failed'>;
  onListContextEntries: (profileId: string, cursor?: string | null) => Promise<ParentContextEntryListView>;
  onContinue: () => void;
  onBack?: () => void;
};

export function ContextScreen(props: Props): React.JSX.Element {
  const snapshot = props.contextRun?.context_snapshot;
  const lessonPin = props.contextRun?.lesson_pin_snapshot;
  const profileId = props.contextRun?.parent_profile_id ?? '';
  const subject = props.contextRun?.subject_label ?? '';
  const subjectConfirmed = Boolean(props.contextRun && subject && isConfirmedRunSubject(props.contextRun, subject));
  const awaitingDrawing = props.contextRun?.current_input_revision === 1
    && (props.contextRun.understanding_revision ?? 0) < 1;
  const [entries, setEntries] = useState<ParentContextEntryListView['context_entries']>([]);
  const [entryCursor, setEntryCursor] = useState<string | null>(null);
  const [entryLoading, setEntryLoading] = useState(false);
  const [entryLoadingMore, setEntryLoadingMore] = useState(false);
  const [entryError, setEntryError] = useState('');
  const [entrySelection, setEntrySelection] = useState<readonly string[] | undefined>(undefined);
  const [selectionNotice, setSelectionNotice] = useState('');
  const [confirming, setConfirming] = useState(false);
  const listEntriesRef = useRef(props.onListContextEntries);
  const isAlreadyConfirmed = props.confirmed || props.contextRun?.context_confirmed === true;

  useEffect(() => { listEntriesRef.current = props.onListContextEntries; }, [props.onListContextEntries]);

  async function loadEntries(cursor: string | null = null, append = false): Promise<void> {
    if (!profileId || isAlreadyConfirmed) return;
    if (append) setEntryLoadingMore(true);
    else setEntryLoading(true);
    setEntryError('');
    try {
      const page = await listEntriesRef.current(profileId, cursor);
      setEntries((current) => append ? mergeEntries(current, page.context_entries) : page.context_entries);
      setEntryCursor(page.next_cursor);
    } catch (cause) {
      setEntryError(safeParentFlowErrorMessage(cause));
    } finally {
      if (append) setEntryLoadingMore(false);
      else setEntryLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    setEntries([]);
    setEntryCursor(null);
    setEntrySelection(undefined);
    setSelectionNotice('');
    if (profileId && !isAlreadyConfirmed) {
      setEntryLoading(true);
      setEntryError('');
      void listEntriesRef.current(profileId).then((page) => {
        if (active) {
          setEntries(page.context_entries);
          setEntryCursor(page.next_cursor);
        }
      }).catch((cause: unknown) => {
        if (active) setEntryError(safeParentFlowErrorMessage(cause));
      }).finally(() => {
        if (active) setEntryLoading(false);
      });
    } else {
      setEntryLoading(false);
      setEntryError('');
    }
    return () => { active = false; };
  }, [profileId, isAlreadyConfirmed]);

  function toggleEntry(contextEntryId: string): void {
    const current = [...(entrySelection ?? [])];
    const index = current.indexOf(contextEntryId);
    if (index >= 0) {
      current.splice(index, 1);
      setEntrySelection(current);
      setSelectionNotice('');
      return;
    }
    if (current.length >= 10) {
      setSelectionNotice('Chỉ chọn tối đa 10 ghi chú.');
      return;
    }
    current.push(contextEntryId);
    setEntrySelection(current);
    setSelectionNotice('');
  }

  async function confirmSelection(): Promise<void> {
    if (confirming || props.busy) return;
    setConfirming(true);
    try {
      const outcome = await props.onConfirm(entrySelection);
      if (outcome === 'entry-not-found') {
        setEntrySelection(undefined);
        await loadEntries();
      }
    } finally {
      setConfirming(false);
    }
  }

  const selectedEntries = snapshot && isParentRunContextSnapshotV2(snapshot) ? snapshot.selected_entries : null;

  return (
    <ScreenFrame
      title="Rà soát thông tin buổi"
      subtitle="Chỉ xem dữ liệu cần cho buổi học này."
      step={props.stepLabel}
      onBack={props.onBack}
      visualTone="creative"
    >
      {props.profile ? <Card variant="creative" style={styles.profileCard}>
        <SectionTitle variant="creative">Hồ sơ được chọn</SectionTitle>
        <Text style={styles.profileText}>
          {props.profile.display_name}
        </Text>
      </Card> : null}

      <Card variant="creative" style={styles.snapshotCard}>
        <SectionTitle variant="creative">Hồ sơ và bản nội dung</SectionTitle>
        {snapshot ? <>
          {props.contextRun?.profile_revision_ref ? <View style={styles.snapshotRow}>
            <Text style={styles.snapshotLabel}>Bản hồ sơ</Text>
            <Text style={styles.snapshotText}>Thông tin hồ sơ đã được lưu cho buổi học này.</Text>
          </View> : null}
          {snapshot.age_months !== undefined ? <View style={styles.snapshotRow}>
            <Text style={styles.snapshotLabel}>Tuổi trong buổi học</Text>
            <Text style={styles.snapshotText}>{snapshot.age_months} tháng</Text>
          </View> : null}
          {snapshot.interests_summary ? <Text style={styles.snapshotInterest}>
            Sở thích được phép dùng: {snapshot.interests_summary}
          </Text> : null}
          <View style={styles.snapshotRow}>
            <Text style={styles.snapshotLabel}>Chủ đề</Text>
            <Text style={styles.snapshotText}>{snapshot.topic || 'Chưa nhập chủ đề.'}</Text>
          </View>
          <View style={styles.snapshotRow}>
            <Text style={styles.snapshotLabel}>Ý tưởng của gia đình</Text>
            <Text style={styles.snapshotTextMuted}>{snapshot.adult_confirmed_idea || 'Chưa có ý tưởng được xác nhận.'}</Text>
          </View>
          {selectedEntries ? <View style={styles.snapshotRow}>
            <Text style={styles.snapshotLabel}>Ghi chú đã chọn ({selectedEntries.length})</Text>
            {selectedEntries.length === 0 ? <Text style={styles.snapshotTextMuted}>Không thêm ghi chú bối cảnh.</Text> : selectedEntries.map((entry, index) => (
              <View key={`${entry.kind}-${index}`} style={styles.selectedEntry}>
                <Text style={styles.snapshotLabel}>{entryKindLabel(entry.kind)}</Text>
                <Text style={styles.snapshotText}>{entry.text}</Text>
              </View>
            ))}
          </View> : null}
          {lessonPin ? <View style={styles.snapshotRow}>
            <Text style={styles.snapshotLabel}>Bài học đã ghim</Text>
            <Text style={styles.snapshotText}>Phiên bản {lessonPin.version_no}</Text>
          </View> : null}
        </> : props.busy ? <ActivityIndicator color={palette.blue} /> : <Text style={styles.snapshotEmpty}>
          Thông tin buổi học sẽ xuất hiện sau khi tạo buổi.
        </Text>}
      </Card>

      {props.contextRun && !subjectConfirmed ? <Notice
        variant="creative"
        text="Hãy xem và xác nhận chủ thể của tranh trước khi xác nhận ngữ cảnh."
        tone="warning"
      /> : null}
      {props.contextRun && !isAlreadyConfirmed ? <Card variant="creative" style={styles.entriesCard}>
        <SectionTitle variant="creative">Ghi chú bối cảnh (tùy chọn)</SectionTitle>
        <Text style={styles.snapshotTextMuted}>Chọn tối đa 10 mục để đưa vào buổi học. Nếu chưa dùng bộ chọn, phần xác nhận hiện tại được giữ nguyên.</Text>
        {entryLoading ? <ActivityIndicator color={palette.blue} /> : null}
        {!entryLoading && entries.length === 0 && !entryError ? <Text style={styles.snapshotTextMuted}>Chưa có ghi chú nào cho hồ sơ này.</Text> : null}
        {entries.map((entry) => {
          const selected = entrySelection?.includes(entry.context_entry_id) ?? false;
          return <TouchableOpacity
            key={entry.context_entry_id}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: selected, disabled: props.busy || confirming }}
            accessibilityLabel={`${entryKindLabel(entry.entry_kind)}. ${entry.short_text}`}
            disabled={props.busy || confirming}
            onPress={() => toggleEntry(entry.context_entry_id)}
            style={[styles.entryChoice, selected && styles.entryChoiceSelected]}
          >
            <View style={styles.entryChoiceMark}>{selected ? <Text style={styles.entryChoiceCheck}>✓</Text> : null}</View>
            <View style={styles.entryChoiceCopy}>
              <View style={styles.entryChoiceMeta}>
                <Text style={styles.snapshotLabel}>{entryKindLabel(entry.entry_kind)}</Text>
                <Text style={styles.entryDate}>{entry.approximate_date ?? entry.created_at.slice(0, 10)}</Text>
              </View>
              <Text style={styles.snapshotText}>{entry.short_text}</Text>
            </View>
          </TouchableOpacity>;
        })}
        {entryCursor ? <SecondaryButton
          label={entryLoadingMore ? 'Đang tải…' : 'Xem thêm ghi chú'}
          disabled={entryLoadingMore || entryLoading || confirming}
          onPress={() => void loadEntries(entryCursor, true)}
        /> : null}
        {entryError ? <Notice variant="creative" text={entryError} tone="warning" /> : null}
        {entryError ? <SecondaryButton variant="creative" label="Tải lại ghi chú" disabled={entryLoading} onPress={() => void loadEntries()} /> : null}
        <Text style={styles.selectionCount}>{entrySelection === undefined ? 'Chưa dùng bộ chọn' : `${entrySelection.length}/10 ghi chú được chọn`}</Text>
        {selectionNotice ? <Notice variant="creative" text={selectionNotice} tone="warning" /> : null}
        <SecondaryButton variant="creative"
          label="Chọn không thêm ghi chú"
          disabled={props.busy || confirming}
          onPress={() => { setEntrySelection([]); setSelectionNotice('Đã chọn không thêm ghi chú.'); }}
        />
      </Card> : null}
      {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}
      {isAlreadyConfirmed ? <>
        <Notice variant="creative" text="Ngữ cảnh đã được xác nhận." tone="success" />
        <SecondaryButton variant="creative" label="Tiếp tục" disabled={props.busy} onPress={props.onContinue} />
      </> : props.contextRun ? <PrimaryButton
        variant="creative"
        label="Xác nhận ngữ cảnh"
        busy={props.busy || confirming}
        disabled={props.busy || confirming || !subjectConfirmed}
        onPress={() => void confirmSelection()}
      /> : <PrimaryButton
        label={props.error ? 'Thử lại' : 'Tạo buổi học'}
        busy={props.busy}
        disabled={props.busy}
        onPress={props.onRetryCreate}
        variant="creative"
      />}
      {awaitingDrawing ? <SecondaryButton
        variant="creative"
        label="Quay lại xem tranh"
        disabled={props.busy}
        onPress={props.onContinue}
      /> : null}
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  profileCard: { backgroundColor: palette.white, gap: 8, minWidth: 0 },
  profileText: { color: palette.ink, fontSize: 16, lineHeight: 22, fontWeight: '700', minWidth: 0, flexShrink: 1 },
  snapshotCard: { backgroundColor: palette.white, gap: 14, minWidth: 0 },
  snapshotRow: { gap: 4, minWidth: 0 },
  snapshotLabel: { color: palette.muted, fontSize: 10, lineHeight: 14, fontWeight: '800', minWidth: 0, flexShrink: 1 },
  snapshotText: { color: palette.ink, fontSize: 14, lineHeight: 21, minWidth: 0, flexShrink: 1 },
  snapshotTextMuted: { color: palette.muted, fontSize: 14, lineHeight: 21, minWidth: 0, flexShrink: 1 },
  snapshotInterest: { color: palette.muted, fontSize: 13, lineHeight: 19, minWidth: 0, flexShrink: 1 },
  snapshotEmpty: { color: palette.muted, fontSize: 13, lineHeight: 18, minWidth: 0, flexShrink: 1 },
  entriesCard: { backgroundColor: palette.white, gap: 12 },
  entryChoice: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, borderWidth: 1, borderColor: palette.border, borderRadius: 12, padding: 11 },
  entryChoiceSelected: { backgroundColor: '#EEF6FC', borderColor: palette.blue },
  entryChoiceMark: { width: 20, height: 20, borderWidth: 1, borderColor: palette.muted, borderRadius: 5, alignItems: 'center', justifyContent: 'center' },
  entryChoiceCheck: { color: palette.blue, fontSize: 14, fontWeight: '800' },
  entryChoiceCopy: { flex: 1, gap: 5, minWidth: 0 },
  entryChoiceMeta: { flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  entryDate: { color: palette.muted, fontSize: 10 },
  selectedEntry: { gap: 3 },
  selectionCount: { color: palette.blue, fontSize: 12, fontWeight: '800' },
});

function mergeEntries(
  current: ParentContextEntryListView['context_entries'],
  incoming: ParentContextEntryListView['context_entries'],
) {
  const ids = new Set(current.map((entry) => entry.context_entry_id));
  return [...current, ...incoming.filter((entry) => !ids.has(entry.context_entry_id))];
}

function entryKindLabel(kind: ParentContextEntryKind): string {
  if (kind === 'OBSERVATION') return 'Quan sát';
  if (kind === 'ACHIEVEMENT') return 'Thành tích';
  return 'Trải nghiệm ngoài ứng dụng';
}
