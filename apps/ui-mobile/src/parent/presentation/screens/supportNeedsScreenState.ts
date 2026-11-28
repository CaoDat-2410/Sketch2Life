import { ParentApplicationError } from '../../application/ParentApplicationError';
import type { ParentSupportNeedsV1, SupportNeedsPutV1 } from '../../domain/types';
import { safeParentFlowErrorMessage } from '../navigation/parentFlowV1';

export type EditableSupportNeedsState = {
  status: 'empty' | 'value';
  revision: number;
  category: string;
  note: string;
  fieldErrors: Partial<Record<'expected_revision' | 'category' | 'note', string>>;
  notice: string;
};

export type SupportNeedsScreenState =
  | { status: 'loading' }
  | { status: 'unavailable' | 'gone' | 'pending-delete' | 'error'; message: string }
  | EditableSupportNeedsState;

export const SUPPORT_NEEDS_UNAVAILABLE_MESSAGE = 'Mục này chưa khả dụng, hãy thử lại sau.';

export function supportNeedsPutInput(revision: number, category: string, note: string): SupportNeedsPutV1 {
  return { expected_revision: revision, category, note };
}

export function clearSensitiveSupportNeedsState(_state: SupportNeedsScreenState): SupportNeedsScreenState {
  return { status: 'loading' };
}

export function supportNeedsStateForLoadFailure(cause: unknown): SupportNeedsScreenState {
  const code = cause instanceof ParentApplicationError ? cause.code : '';
  const status = cause instanceof ParentApplicationError ? cause.status : undefined;
  if (code === 'SUPPORT_NEEDS_UNAVAILABLE' || status === 503) {
    return { status: 'unavailable', message: SUPPORT_NEEDS_UNAVAILABLE_MESSAGE };
  }
  if (code === 'PROFILE_NOT_FOUND' || status === 404) {
    return { status: 'gone', message: 'Hồ sơ không còn khả dụng.' };
  }
  return { status: 'error', message: safeParentFlowErrorMessage(cause) };
}

export function supportNeedsFieldMessage(code: string): string {
  if (code === 'DIAGNOSIS_LIKE') return 'Nội dung không nên nêu chẩn đoán.';
  if (code === 'TOO_LONG') return 'Nội dung dài quá. Hãy rút gọn rồi thử lại.';
  if (code === 'EMPTY' || code === 'REQUIRED') return 'Hãy nhập ít nhất một nội dung cần hỗ trợ.';
  return 'Hãy kiểm tra lại nội dung cần hỗ trợ.';
}

export function stateFromSupportNeeds(value: ParentSupportNeedsV1, notice: string): EditableSupportNeedsState {
  return {
    status: value.revision === 0 ? 'empty' : 'value',
    revision: value.revision,
    category: value.category ?? '',
    note: value.note ?? '',
    fieldErrors: {},
    notice,
  };
}
