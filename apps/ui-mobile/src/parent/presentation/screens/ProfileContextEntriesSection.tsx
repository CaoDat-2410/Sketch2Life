import React, { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import type {
  CreateParentContextEntryRequest,
  ParentContextEntryEnvelope,
  ParentContextEntryKind,
  ParentContextEntryListView,
} from '../../domain/types';
import { validateContextEntryRequest, visibleCharacterCount } from '../../application/parentProfileInputValidation';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import { safeParentFlowErrorMessage } from '../navigation/parentFlowV1';
import { Card, Field, Notice, PrimaryButton, SectionTitle, SecondaryButton, palette } from '../components/ui';

type Props = {
  profileId: string;
  newActionIdentity: () => string;
  onList: (profileId: string, cursor?: string | null) => Promise<ParentContextEntryListView>;
  onCreate: (
    profileId: string,
    input: CreateParentContextEntryRequest,
    actionIdentity: string,
  ) => Promise<ParentContextEntryEnvelope>;
};

const ENTRY_KINDS: Array<{ value: ParentContextEntryKind; label: string }> = [
  { value: 'OBSERVATION', label: 'Quan sát' },
  { value: 'ACHIEVEMENT', label: 'Thành tích' },
  { value: 'OUTSIDE_EXPERIENCE', label: 'Trải nghiệm ngoài ứng dụng' },
];

export function ProfileContextEntriesSection({ profileId, newActionIdentity, onList, onCreate }: Props): React.JSX.Element {
  const [entries, setEntries] = useState<ParentContextEntryListView['context_entries']>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [listError, setListError] = useState('');
  const [formError, setFormError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [entryKind, setEntryKind] = useState<ParentContextEntryKind>('OBSERVATION');
  const [shortText, setShortText] = useState('');
  const [approximateDate, setApproximateDate] = useState('');
  const onListRef = useRef(onList);
  const actionIdentityRef = useRef<string | null>(null);
  const submitInFlight = useRef(false);

  useEffect(() => { onListRef.current = onList; }, [onList]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setEntries([]);
    setNextCursor(null);
    setListError('');
    void onListRef.current(profileId).then((page) => {
      if (!active) return;
      setEntries(page.context_entries);
      setNextCursor(page.next_cursor);
    }).catch((cause: unknown) => {
      if (active) setListError(contextEntryListError(cause));
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [profileId]);

  function updateShortText(value: string): void {
    setShortText(Array.from(value).slice(0, 500).join(''));
    actionIdentityRef.current = null;
    setFieldErrors({});
    setFormError('');
  }

  function updateApproximateDate(value: string): void {
    setApproximateDate(value.slice(0, 10));
    actionIdentityRef.current = null;
    setFieldErrors({});
    setFormError('');
  }

  function makeRequest(): CreateParentContextEntryRequest {
    return {
      entry_kind: entryKind,
      short_text: shortText.trim(),
      source_kind: 'PARENT_ENTERED',
      ...(approximateDate.trim() ? { approximate_date: approximateDate.trim() } : {}),
    };
  }

  async function loadPage(cursor: string | null, append: boolean): Promise<void> {
    if (append) setLoadingMore(true);
    else setLoading(true);
    setListError('');
    try {
      const page = await onListRef.current(profileId, cursor);
      setEntries((current) => append
        ? mergeEntries(current, page.context_entries)
        : page.context_entries);
      setNextCursor(page.next_cursor);
    } catch (cause) {
      setListError(contextEntryListError(cause));
    } finally {
      if (append) setLoadingMore(false);
      else setLoading(false);
    }
  }

  async function submit(): Promise<void> {
    if (busy || submitInFlight.current) return;
    const input = makeRequest();
    const validation = validateContextEntryRequest(input);
    if (validation.length > 0) {
      setFieldErrors(Object.fromEntries(validation.map((error) => [error.field, contextEntryFieldMessage(error.code)])));
      setFormError('');
      return;
    }
    submitInFlight.current = true;
    setBusy(true);
    setFormError('');
    setFieldErrors({});
    const actionIdentity = actionIdentityRef.current ?? newActionIdentity();
    actionIdentityRef.current = actionIdentity;
    try {
      await onCreate(profileId, input, actionIdentity);
      actionIdentityRef.current = null;
      setShortText('');
      setApproximateDate('');
      setFieldErrors({});
      await loadPage(null, false);
    } catch (cause) {
      setFieldErrors(readContextEntryFieldErrors(cause));
      setFormError(safeParentFlowErrorMessage(cause));
    } finally {
      submitInFlight.current = false;
      setBusy(false);
    }
  }

  const characterCount = visibleCharacterCount(shortText);
  const request = makeRequest();
  const formValid = validateContextEntryRequest(request).length === 0;

  return (
    <Card style={styles.card}>
      <SectionTitle>Ghi chú bối cảnh</SectionTitle>
      <Text style={styles.helper}>Chỉ lưu thông tin do người lớn nhập. Ghi chú được giữ nguyên theo từng lần thêm.</Text>

      {loading ? <Text style={styles.muted}>Đang tải ghi chú…</Text> : null}
      {!loading && entries.length === 0 && !listError ? <Text style={styles.muted}>Chưa có ghi chú nào.</Text> : null}
      {entries.map((entry) => (
        <View key={entry.context_entry_id} style={styles.entryRow}>
          <View style={styles.entryMeta}>
            <Text style={styles.kindLabel}>{entryKindLabel(entry.entry_kind)}</Text>
            <Text style={styles.dateLabel}>{entry.approximate_date ?? formatDate(entry.created_at)}</Text>
          </View>
          <Text style={styles.entryText}>{entry.short_text}</Text>
        </View>
      ))}
      {listError ? <Notice text={listError} tone="warning" /> : null}
      {listError ? <SecondaryButton label="Tải lại ghi chú" disabled={loading} onPress={() => void loadPage(null, false)} /> : null}
      {nextCursor ? <SecondaryButton
        label={loadingMore ? 'Đang tải…' : 'Xem thêm'}
        disabled={loadingMore || loading}
        onPress={() => void loadPage(nextCursor, true)}
      /> : null}

      <View style={styles.formDivider} />
      <Text style={styles.formTitle}>Thêm ghi chú</Text>
      <View style={styles.kindChoices}>
        {ENTRY_KINDS.map((kind) => {
          const selected = kind.value === entryKind;
          return <TouchableOpacity
            key={kind.value}
            accessibilityRole="button"
            accessibilityState={{ selected }}
            accessibilityLabel={kind.label}
            onPress={() => {
              setEntryKind(kind.value);
              actionIdentityRef.current = null;
            }}
            style={[styles.kindChoice, selected && styles.kindChoiceSelected]}
          >
            <Text style={[styles.kindChoiceText, selected && styles.kindChoiceTextSelected]}>{kind.label}</Text>
          </TouchableOpacity>;
        })}
      </View>
      <Field
        label="Nội dung"
        accessibilityLabel="Nội dung ghi chú"
        value={shortText}
        onChangeText={updateShortText}
        placeholder="Nhập ghi chú ngắn"
        multiline
        maxLength={1000}
        textAlignVertical="top"
        style={styles.textInput}
      />
      <Text style={styles.counter}>{characterCount}/500 ký tự</Text>
      {fieldErrors.short_text ? <Notice text={fieldErrors.short_text} tone="error" /> : null}
      <Field
        label="Ngày gần đúng (không bắt buộc)"
        accessibilityLabel="Ngày gần đúng"
        value={approximateDate}
        onChangeText={updateApproximateDate}
        placeholder="YYYY-MM-DD"
        maxLength={10}
        autoCapitalize="none"
        style={styles.dateInput}
      />
      {fieldErrors.approximate_date ? <Notice text={fieldErrors.approximate_date} tone="error" /> : null}
      {formError ? <Notice text={formError} tone="error" /> : null}
      <PrimaryButton label="Lưu ghi chú" busy={busy} disabled={!formValid || busy} onPress={() => void submit()} />
    </Card>
  );
}

function mergeEntries(current: ParentContextEntryListView['context_entries'], incoming: ParentContextEntryListView['context_entries']) {
  const ids = new Set(current.map((entry) => entry.context_entry_id));
  return [...current, ...incoming.filter((entry) => !ids.has(entry.context_entry_id))];
}

function entryKindLabel(kind: ParentContextEntryKind): string {
  return ENTRY_KINDS.find((item) => item.value === kind)?.label ?? 'Ghi chú';
}

function formatDate(value: string): string {
  const date = value.slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/u.test(date) ? date : 'Ngày đã ghi';
}

function contextEntryListError(cause: unknown): string {
  return safeParentFlowErrorMessage(cause);
}

function readContextEntryFieldErrors(cause: unknown): Record<string, string> {
  if (!(cause instanceof ParentApplicationError)) return {};
  const result: Record<string, string> = {};
  for (const error of cause.fieldErrors ?? []) {
    if (['short_text', 'approximate_date', 'entry_kind'].includes(error.field)) {
      result[error.field] = contextEntryFieldMessage(error.code);
    }
  }
  return result;
}

function contextEntryFieldMessage(code: string): string {
  if (code === 'EMPTY' || code === 'REQUIRED') return 'Nhập nội dung ghi chú.';
  if (code === 'TOO_LONG') return 'Ghi chú dài quá. Hãy rút gọn rồi thử lại.';
  if (code === 'INVALID_FORMAT') return 'Kiểm tra lại định dạng nội dung hoặc ngày.';
  return 'Kiểm tra lại thông tin ghi chú.';
}

const styles = StyleSheet.create({
  card: { backgroundColor: palette.white, gap: 12 },
  helper: { color: palette.muted, fontSize: 12, lineHeight: 18 },
  muted: { color: palette.muted, fontSize: 13, lineHeight: 19 },
  entryRow: { gap: 6, borderTopWidth: 1, borderTopColor: palette.border, paddingTop: 10 },
  entryMeta: { flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  kindLabel: { color: palette.ink, fontSize: 12, fontWeight: '800', flexShrink: 1 },
  dateLabel: { color: palette.muted, fontSize: 11 },
  entryText: { color: palette.ink, fontSize: 13, lineHeight: 19 },
  formDivider: { height: 1, backgroundColor: palette.border, marginVertical: 4 },
  formTitle: { color: palette.ink, fontSize: 14, fontWeight: '800' },
  kindChoices: { gap: 7 },
  kindChoice: { borderRadius: 12, borderWidth: 1, borderColor: palette.border, paddingVertical: 9, paddingHorizontal: 12 },
  kindChoiceSelected: { borderColor: palette.blue, backgroundColor: '#EFF6FF' },
  kindChoiceText: { color: palette.ink, fontSize: 12, lineHeight: 17 },
  kindChoiceTextSelected: { color: palette.blue, fontWeight: '800' },
  textInput: { minHeight: 88 },
  counter: { color: palette.muted, fontSize: 11, textAlign: 'right' },
  dateInput: { minHeight: 44 },
});
