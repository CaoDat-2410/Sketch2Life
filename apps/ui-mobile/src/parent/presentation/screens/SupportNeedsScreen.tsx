import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import type { ParentSupportNeedsV1, ParentSupportNeedsWriteV1, SupportNeedsPutV1 } from '../../domain/types';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import { validateSupportNeedsPut, visibleCharacterCount } from '../../application/parentProfileInputValidation';
import { safeParentFlowErrorMessage } from '../navigation/parentFlowV1';
import {
  clearSensitiveSupportNeedsState,
  stateFromSupportNeeds,
  supportNeedsPutInput,
  supportNeedsFieldMessage,
  supportNeedsStateForLoadFailure,
  SUPPORT_NEEDS_UNAVAILABLE_MESSAGE,
  type EditableSupportNeedsState,
  type SupportNeedsScreenState,
} from './supportNeedsScreenState';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SecondaryButton, palette } from '../components/ui';
const STALE_REVIEW_MESSAGE = 'Dữ liệu đã thay đổi. Hãy xem lại nội dung mới nhất trước khi lưu.';

type Props = {
  profileId: string;
  newActionIdentity: () => string;
  onLoad: (profileId: string) => Promise<ParentSupportNeedsV1>;
  onSave: (profileId: string, input: SupportNeedsPutV1, actionIdentity: string) => Promise<ParentSupportNeedsWriteV1>;
  onBack: () => void;
};

const EMPTY_SCREEN_STATE: SupportNeedsScreenState = { status: 'loading' };

export function SupportNeedsScreen({ profileId, newActionIdentity, onLoad, onSave, onBack }: Props): React.JSX.Element {
  const [screenState, setScreenState] = useState<SupportNeedsScreenState>(EMPTY_SCREEN_STATE);
  const [saving, setSaving] = useState(false);
  const stateRef = useRef<SupportNeedsScreenState>(EMPTY_SCREEN_STATE);
  const actionIdentityRef = useRef<string | null>(null);
  const saveInFlight = useRef(false);
  const onLoadRef = useRef(onLoad);
  const onSaveRef = useRef(onSave);

  useEffect(() => { onLoadRef.current = onLoad; }, [onLoad]);
  useEffect(() => { onSaveRef.current = onSave; }, [onSave]);

  function updateState(next: SupportNeedsScreenState): void {
    stateRef.current = next;
    setScreenState(next);
  }

  async function load(profile: string, showStaleReview = false, isActive: () => boolean = () => true): Promise<void> {
    updateState({ status: 'loading' });
    try {
      const needs = await onLoadRef.current(profile);
      if (!isActive()) return;
      updateState(stateFromSupportNeeds(needs, showStaleReview ? STALE_REVIEW_MESSAGE : ''));
    } catch (cause) {
      if (isActive()) updateState(supportNeedsStateForLoadFailure(cause));
    }
  }

  useEffect(() => {
    let active = true;
    actionIdentityRef.current = null;
    void load(profileId, false, () => active);
    return () => {
      active = false;
      actionIdentityRef.current = null;
      stateRef.current = clearSensitiveSupportNeedsState(stateRef.current);
    };
  }, [profileId]);

  function leave(): void {
    actionIdentityRef.current = null;
    updateState(clearSensitiveSupportNeedsState(stateRef.current));
    onBack();
  }

  function updateEditable(field: 'category' | 'note', value: string): void {
    actionIdentityRef.current = null;
    const current = stateRef.current;
    if (current.status !== 'empty' && current.status !== 'value') return;
    const limit = field === 'category' ? 80 : 2000;
    const boundedValue = Array.from(value).slice(0, limit).join('');
    updateState({
      ...current,
      [field]: boundedValue,
      fieldErrors: { ...current.fieldErrors, [field]: undefined },
      notice: '',
    });
  }

  async function submit(): Promise<void> {
    const current = stateRef.current;
    if ((current.status !== 'empty' && current.status !== 'value') || saveInFlight.current) return;
    const input: SupportNeedsPutV1 = supportNeedsPutInput(current.revision, current.category, current.note);
    const validation = validateSupportNeedsPut(input);
    if (validation.length > 0) {
      const nextErrors: EditableSupportNeedsState['fieldErrors'] = {};
      for (const error of validation) {
        if (error.field === 'category' || error.field === 'note' || error.field === 'expected_revision') {
          nextErrors[error.field] = supportNeedsFieldMessage(error.code);
        }
      }
      updateState({ ...current, fieldErrors: nextErrors, notice: '' });
      return;
    }

    saveInFlight.current = true;
    setSaving(true);
    const actionIdentity = actionIdentityRef.current ?? newActionIdentity();
    actionIdentityRef.current = actionIdentity;
    try {
      const receipt = await onSaveRef.current(profileId, input, actionIdentity);
      actionIdentityRef.current = null;
      updateState({
        status: 'value',
        revision: receipt.revision,
        category: current.category,
        note: current.note,
        fieldErrors: {},
        notice: 'Đã lưu thay đổi.',
      });
    } catch (cause) {
      const errorCode = cause instanceof ParentApplicationError ? cause.code : '';
      const status = cause instanceof ParentApplicationError ? cause.status : undefined;
      if (errorCode === 'SUPPORT_NEEDS_UNAVAILABLE' || status === 503) {
        updateState({ status: 'unavailable', message: SUPPORT_NEEDS_UNAVAILABLE_MESSAGE });
      } else if (errorCode === 'PROFILE_NOT_FOUND' || status === 404) {
        updateState({ status: 'gone', message: 'Hồ sơ không còn khả dụng.' });
      } else if (errorCode === 'INVALID_STATE_TRANSITION' && status === 409) {
        updateState({ status: 'pending-delete', message: 'Hồ sơ đang chờ xóa. Nội dung đã được xóa khỏi màn hình.' });
      } else if (errorCode === 'STALE_REVISION' && status === 409) {
        actionIdentityRef.current = null;
        await load(profileId, true);
      } else {
        const fieldErrors: EditableSupportNeedsState['fieldErrors'] = {};
        for (const error of cause instanceof ParentApplicationError ? cause.fieldErrors ?? [] : []) {
          if (error.field === 'category' || error.field === 'note' || error.field === 'expected_revision') {
            fieldErrors[error.field] = supportNeedsFieldMessage(error.code);
          }
        }
        updateState({
          ...current,
          fieldErrors,
          notice: safeParentFlowErrorMessage(cause),
        });
      }
    } finally {
      saveInFlight.current = false;
      setSaving(false);
    }
  }

  const editable = screenState.status === 'empty' || screenState.status === 'value' ? screenState : null;
  const putInput = editable
    ? supportNeedsPutInput(editable.revision, editable.category, editable.note)
    : null;
  const canSave = Boolean(putInput && validateSupportNeedsPut(putInput).length === 0 && !saving);

  return (
    <ScreenFrame
      title="Nhu cầu hỗ trợ"
      subtitle="Thông tin do người lớn nhập, mặc định không dùng cho nội dung AI."
      onBack={leave}
      backDisabled={saving}
    >
      {screenState.status === 'loading' ? <Card style={styles.card}><ActivityIndicator color={palette.blue} /><Text style={styles.body}>Đang tải mục này…</Text></Card> : null}
      {screenState.status === 'unavailable' ? <Card style={styles.card}>
        <Notice text={SUPPORT_NEEDS_UNAVAILABLE_MESSAGE} tone="info" />
        <SecondaryButton label="Thử lại sau" onPress={() => void load(profileId)} />
      </Card> : null}
      {screenState.status === 'gone' || screenState.status === 'pending-delete' ? <Card style={styles.card}>
        <Notice text={screenState.message} tone="warning" />
      </Card> : null}
      {screenState.status === 'error' ? <Card style={styles.card}>
        <Notice text={screenState.message} tone="warning" />
        <SecondaryButton label="Tải lại" onPress={() => void load(profileId)} />
      </Card> : null}
      {editable ? <Card style={styles.card}>
        <Text style={styles.body}>{editable.revision === 0 ? 'Chưa có thông tin được lưu.' : `Phiên bản ${editable.revision}`}</Text>
        {editable.notice ? <Notice text={editable.notice} tone="info" /> : null}
        <Field
          label="Nhu cầu hỗ trợ"
          accessibilityLabel="Nhu cầu hỗ trợ"
          value={editable.category}
          onChangeText={(value) => updateEditable('category', value)}
          placeholder="Ví dụ: điều cần lưu ý khi học"
          maxLength={160}
          style={styles.input}
        />
        <Text style={styles.counter}>{visibleCharacterCount(editable.category)}/80 ký tự</Text>
        {editable.fieldErrors.category ? <Notice text={editable.fieldErrors.category} tone="error" /> : null}
        <Field
          label="Ghi chú"
          accessibilityLabel="Ghi chú nhu cầu hỗ trợ"
          value={editable.note}
          onChangeText={(value) => updateEditable('note', value)}
          placeholder="Chỉ nhập điều cần thiết"
          multiline
          maxLength={4000}
          textAlignVertical="top"
          style={styles.noteInput}
        />
        <Text style={styles.counter}>{visibleCharacterCount(editable.note)}/2000 ký tự</Text>
        {editable.fieldErrors.note ? <Notice text={editable.fieldErrors.note} tone="error" /> : null}
        {editable.fieldErrors.expected_revision ? <Notice text={editable.fieldErrors.expected_revision} tone="error" /> : null}
        <Text style={styles.privacy}>Nội dung không được gửi vào ngữ cảnh AI theo mặc định.</Text>
        <PrimaryButton label="Lưu thay đổi" disabled={!canSave} busy={saving} onPress={() => void submit()} />
      </Card> : null}
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: palette.white, gap: 12 },
  body: { color: palette.ink, fontSize: 13, lineHeight: 19 },
  input: { minHeight: 44 },
  noteInput: { minHeight: 110 },
  counter: { color: palette.muted, fontSize: 11, textAlign: 'right' },
  privacy: { color: palette.muted, fontSize: 11, lineHeight: 16 },
});
