import { describe, expect, it } from 'vitest';
import {
  buildSubjectRolesRequest,
  initialSubjectRoles,
  mainSubjectLabel,
  promoteToMain,
  setRoleLabel,
  toggleSecondaryUse,
} from '../src/parent/domain/subjectRoles';
import type { ParentDrawingCandidateV1 } from '../src/parent/domain/types';
import { readDrawingCandidate } from '../src/parent/presentation/navigation/parentFlowV1';

const candidate = (extra: Partial<ParentDrawingCandidateV1> = {}): ParentDrawingCandidateV1 => ({
  candidate_subject: 'con rùa',
  visible_features: ['mai ba ô tròn'],
  confidence: 0.8,
  adult_confirmation_required: true,
  decision: 'REVIEW_REQUIRED',
  entities: [
    { entity_id: 'main', label: 'con rùa', suggested_role: 'main' },
    { entity_id: 'sec-1', label: 'chiếc lá', suggested_role: 'secondary' },
    { entity_id: 'sec-2', label: 'bông hoa', suggested_role: 'secondary' },
  ],
  subject_roles: null,
  ...extra,
});

describe('initialSubjectRoles', () => {
  it('turns AI entities into editable roles with every secondary used by default', () => {
    expect(initialSubjectRoles(candidate())).toEqual([
      { entity_id: 'main', label: 'con rùa', role: 'main' },
      { entity_id: 'sec-1', label: 'chiếc lá', role: 'secondary' },
      { entity_id: 'sec-2', label: 'bông hoa', role: 'secondary' },
    ]);
  });

  it('resumes the roles an adult already approved', () => {
    const saved = [
      { entity_id: 'main' as const, label: 'rùa nhỏ', role: 'main' as const },
      { entity_id: 'sec-1' as const, label: 'chiếc lá', role: 'excluded' as const },
      { entity_id: 'sec-2' as const, label: 'bông hoa', role: 'secondary' as const },
    ];
    expect(initialSubjectRoles(candidate({ subject_roles: saved }))).toEqual(saved);
  });

  it('is empty for a drawing analysed before roles existed', () => {
    expect(initialSubjectRoles(candidate({ entities: undefined, subject_roles: undefined }))).toEqual([]);
    expect(initialSubjectRoles(candidate({ entities: [] }))).toEqual([]);
  });
});

describe('editing roles', () => {
  const base = () => initialSubjectRoles(candidate());

  it('renames one object without touching the others', () => {
    const next = setRoleLabel(base(), 'sec-1', 'lá xanh');
    expect(next.find((r) => r.entity_id === 'sec-1')?.label).toBe('lá xanh');
    expect(next.find((r) => r.entity_id === 'main')?.label).toBe('con rùa');
  });

  it('toggles a secondary between used and excluded but never the main subject', () => {
    const off = toggleSecondaryUse(base(), 'sec-1');
    expect(off.find((r) => r.entity_id === 'sec-1')?.role).toBe('excluded');
    expect(toggleSecondaryUse(off, 'sec-1').find((r) => r.entity_id === 'sec-1')?.role).toBe('secondary');
    expect(toggleSecondaryUse(base(), 'main')).toEqual(base());
  });

  it('promotes a secondary to main and demotes the old main to a used secondary', () => {
    const next = promoteToMain(base(), 'sec-1', 'rùa đang ăn');
    expect(next.find((r) => r.entity_id === 'sec-1')?.role).toBe('main');
    expect(next.find((r) => r.entity_id === 'main')).toEqual({
      entity_id: 'main',
      label: 'rùa đang ăn',
      role: 'secondary',
    });
    expect(next.filter((r) => r.role === 'main')).toHaveLength(1);
    expect(mainSubjectLabel(next)).toBe('chiếc lá');
  });

  it('promoting an excluded object makes it main and keeps the old main used', () => {
    const excluded = toggleSecondaryUse(base(), 'sec-2');
    const next = promoteToMain(excluded, 'sec-2', 'con rùa');
    expect(next.find((r) => r.entity_id === 'sec-2')?.role).toBe('main');
    expect(next.find((r) => r.entity_id === 'main')?.role).toBe('secondary');
  });

  it('does not mutate its input', () => {
    const original = base();
    const snapshot = JSON.stringify(original);
    promoteToMain(original, 'sec-1', 'x');
    toggleSecondaryUse(original, 'sec-2');
    setRoleLabel(original, 'main', 'y');
    expect(JSON.stringify(original)).toBe(snapshot);
  });
});

describe('buildSubjectRolesRequest', () => {
  it('sends nothing for drawings without entities so older runs keep working', () => {
    expect(buildSubjectRolesRequest([], 'con rùa')).toEqual({ kind: 'none' });
  });

  it('uses the edited subject field as the main label and trims labels', () => {
    const roles = setRoleLabel(initialSubjectRoles(candidate()), 'sec-1', '  lá xanh  ');
    expect(buildSubjectRolesRequest(roles, '  rùa nhỏ ')).toEqual({
      kind: 'ok',
      roles: [
        { entity_id: 'main', label: 'rùa nhỏ', role: 'main' },
        { entity_id: 'sec-1', label: 'lá xanh', role: 'secondary' },
        { entity_id: 'sec-2', label: 'bông hoa', role: 'secondary' },
      ],
    });
  });

  it.each([
    ['empty used label', (r: ReturnType<typeof initialSubjectRoles>) => setRoleLabel(r, 'sec-1', '   ')],
    ['label over 100 chars', (r: ReturnType<typeof initialSubjectRoles>) => setRoleLabel(r, 'sec-1', 'a'.repeat(101))],
    ['duplicate used labels', (r: ReturnType<typeof initialSubjectRoles>) => setRoleLabel(r, 'sec-1', 'Con  Rùa')],
  ])('refuses %s', (_name, mutate) => {
    const result = buildSubjectRolesRequest(mutate(initialSubjectRoles(candidate())), 'con rùa');
    expect(result.kind).toBe('invalid');
  });

  it('does not block on an empty label of an excluded object', () => {
    const roles = setRoleLabel(toggleSecondaryUse(initialSubjectRoles(candidate()), 'sec-1'), 'sec-1', '');
    const result = buildSubjectRolesRequest(roles, 'con rùa');
    expect(result.kind).toBe('ok');
    if (result.kind === 'ok') expect(result.roles.find((r) => r.entity_id === 'sec-1')?.label.length).toBeGreaterThan(0);
  });
});

describe('readDrawingCandidate keeps role data', () => {
  const wire = {
    candidate_subject: 'con rùa',
    visible_features: ['mai'],
    confidence: 0.8,
    adult_confirmation_required: true,
    decision: 'REVIEW_REQUIRED',
  };

  it('passes entities and approved roles through', () => {
    const read = readDrawingCandidate({
      ...wire,
      entities: [{ entity_id: 'main', label: 'con rùa', suggested_role: 'main' }],
      subject_roles: [{ entity_id: 'main', label: 'con rùa', role: 'main' }],
    });
    expect(read?.entities).toHaveLength(1);
    expect(read?.subject_roles).toEqual([{ entity_id: 'main', label: 'con rùa', role: 'main' }]);
  });

  it('drops malformed role data instead of trusting it, and omits the keys when absent', () => {
    const bad = readDrawingCandidate({ ...wire, entities: [{ entity_id: 'x', label: 1 }], subject_roles: 'nope' });
    expect(bad?.entities ?? []).toEqual([]);
    expect(bad?.subject_roles ?? null).toBeNull();
    expect(Object.keys(readDrawingCandidate(wire) ?? {})).not.toContain('entities');
  });
});
