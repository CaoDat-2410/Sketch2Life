import type { CreateParentContextEntryRequest, ParentContextEntryKind, SupportNeedsPutV1 } from '../domain/types';
import type { ParentSafeFieldError } from './ParentApplicationError';

const CONTEXT_ENTRY_KINDS = new Set<ParentContextEntryKind>([
  'OBSERVATION', 'ACHIEVEMENT', 'OUTSIDE_EXPERIENCE',
]);
const DISALLOWED_CONTEXT_CONTROL = /[\u0000-\u0008\u000B\u000C\u000E-\u001F]/u;
const DISALLOWED_SUPPORT_CONTROL = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/u;

export function visibleCharacterCount(value: string): number {
  return Array.from(value).length;
}

export function utf8ByteLength(value: string): number {
  return encodeURIComponent(value).replace(/%[0-9A-F]{2}/giu, 'x').length;
}

export function validateContextEntryRequest(input: CreateParentContextEntryRequest): ParentSafeFieldError[] {
  const errors: ParentSafeFieldError[] = [];
  if (!CONTEXT_ENTRY_KINDS.has(input.entry_kind)) errors.push({ field: 'entry_kind', code: 'INVALID_VALUE' });
  if (typeof input.short_text !== 'string' || input.short_text.trim().length === 0) {
    errors.push({ field: 'short_text', code: 'EMPTY' });
  } else {
    const characters = visibleCharacterCount(input.short_text);
    if (characters > 500 || utf8ByteLength(input.short_text) > 2000) {
      errors.push({ field: 'short_text', code: 'TOO_LONG' });
    }
    if (DISALLOWED_CONTEXT_CONTROL.test(input.short_text)) {
      errors.push({ field: 'short_text', code: 'INVALID_FORMAT' });
    }
  }
  if (typeof input.source_kind !== 'string' || !/^[A-Z][A-Z0-9_]{0,31}$/u.test(input.source_kind)) {
    errors.push({ field: 'source_kind', code: 'INVALID_FORMAT' });
  }
  if (input.approximate_date !== undefined && !isCalendarDate(input.approximate_date)) {
    errors.push({ field: 'approximate_date', code: 'INVALID_FORMAT' });
  }
  return errors;
}

export function validateSupportNeedsPut(input: SupportNeedsPutV1): ParentSafeFieldError[] {
  const errors: ParentSafeFieldError[] = [];
  if (!Number.isInteger(input.expected_revision) || input.expected_revision < 0 || input.expected_revision > 2_147_483_647) {
    errors.push({ field: 'expected_revision', code: 'OUT_OF_RANGE' });
  }

  validateSupportNeedsText(input.category, 'category', 80, 320, errors);
  validateSupportNeedsText(input.note, 'note', 2000, 8000, errors);
  if ((input.category ?? '').trim().length === 0 && (input.note ?? '').trim().length === 0) {
    errors.push({ field: 'category', code: 'EMPTY' }, { field: 'note', code: 'EMPTY' });
  }
  return errors;
}

function validateSupportNeedsText(
  value: string | null,
  field: 'category' | 'note',
  maxCharacters: number,
  maxBytes: number,
  errors: ParentSafeFieldError[],
): void {
  if (value === null) return;
  if (typeof value !== 'string') {
    errors.push({ field, code: 'INVALID_TYPE' });
    return;
  }
  if (visibleCharacterCount(value) > maxCharacters || utf8ByteLength(value) > maxBytes) {
    errors.push({ field, code: 'TOO_LONG' });
  }
  if (DISALLOWED_SUPPORT_CONTROL.test(value)) errors.push({ field, code: 'INVALID_FORMAT' });
}

function isCalendarDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/u.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}
