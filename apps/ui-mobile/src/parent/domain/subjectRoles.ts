import type {
  ParentDrawingCandidateV1,
  ParentSubjectEntityIdV1,
  ParentSubjectRoleV1,
} from './types';

export const MAX_ROLE_LABEL_LENGTH = 100;

export type SubjectRolesRequest =
  | { kind: 'none' }
  | { kind: 'ok'; roles: ParentSubjectRoleV1[] }
  | { kind: 'invalid'; reason: 'LABEL_EMPTY' | 'LABEL_TOO_LONG' | 'LABEL_DUPLICATE' | 'MAIN_MISSING' };

function normalizeLabel(value: string): string {
  return value
    .toLowerCase()
    .replace(/đ/g, 'd')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Editable roles for the review screen; empty when the drawing has no AI entities (older runs). */
export function initialSubjectRoles(candidate: ParentDrawingCandidateV1): ParentSubjectRoleV1[] {
  if (candidate.subject_roles && candidate.subject_roles.length > 0) {
    return candidate.subject_roles.map((role) => ({ ...role }));
  }
  return (candidate.entities ?? []).map((entity) => ({
    entity_id: entity.entity_id,
    label: entity.label,
    role: entity.suggested_role,
  }));
}

export function mainSubjectLabel(roles: ReadonlyArray<ParentSubjectRoleV1>): string {
  return roles.find((role) => role.role === 'main')?.label ?? '';
}

export function setRoleLabel(
  roles: ReadonlyArray<ParentSubjectRoleV1>,
  entityId: ParentSubjectEntityIdV1,
  label: string,
): ParentSubjectRoleV1[] {
  return roles.map((role) => (role.entity_id === entityId ? { ...role, label } : { ...role }));
}

/** "Dùng trong truyện" switch: a secondary is either used or excluded; the main subject stays. */
export function toggleSecondaryUse(
  roles: ReadonlyArray<ParentSubjectRoleV1>,
  entityId: ParentSubjectEntityIdV1,
): ParentSubjectRoleV1[] {
  return roles.map((role) => {
    if (role.entity_id !== entityId || role.role === 'main') return { ...role };
    return { ...role, role: role.role === 'secondary' ? 'excluded' : 'secondary' };
  });
}

/** Makes one object the main subject; the previous main becomes a used secondary. */
export function promoteToMain(
  roles: ReadonlyArray<ParentSubjectRoleV1>,
  entityId: ParentSubjectEntityIdV1,
  currentMainLabel: string,
): ParentSubjectRoleV1[] {
  return roles.map((role) => {
    if (role.entity_id === entityId) return { ...role, role: 'main' };
    if (role.role === 'main') return { ...role, label: currentMainLabel, role: 'secondary' };
    return { ...role };
  });
}

/** Payload for the subject confirmation: the subject field is the main label (SRS: adult edits). */
export function buildSubjectRolesRequest(
  roles: ReadonlyArray<ParentSubjectRoleV1>,
  subject: string,
): SubjectRolesRequest {
  if (roles.length === 0) return { kind: 'none' };
  if (!roles.some((role) => role.role === 'main')) return { kind: 'invalid', reason: 'MAIN_MISSING' };
  const trimmed = roles.map((role) => ({
    ...role,
    label: (role.role === 'main' ? subject : role.label).trim(),
  }));
  const used = trimmed.filter((role) => role.role !== 'excluded');
  if (used.some((role) => role.label.length === 0)) return { kind: 'invalid', reason: 'LABEL_EMPTY' };
  if (used.some((role) => role.label.length > MAX_ROLE_LABEL_LENGTH)) return { kind: 'invalid', reason: 'LABEL_TOO_LONG' };
  const keys = used.map((role) => normalizeLabel(role.label));
  if (new Set(keys).size !== keys.length) return { kind: 'invalid', reason: 'LABEL_DUPLICATE' };
  // An excluded object is never used, but the server still needs a valid label for it.
  return {
    kind: 'ok',
    roles: trimmed.map((role) => (role.label.length === 0 && role.role === 'excluded'
      ? { ...role, label: 'vật khác' }
      : { ...role, label: role.label.slice(0, MAX_ROLE_LABEL_LENGTH) })),
  };
}
