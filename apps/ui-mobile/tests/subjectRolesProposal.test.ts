import { describe, expect, it } from 'vitest';
import { initialSubjectRoles, mainChoiceRequired, mainSubjectLabel } from '../src/parent/domain/subjectRoles';
import type { ParentDrawingCandidateV1 } from '../src/parent/domain/types';
import { readDrawingCandidate } from '../src/parent/presentation/navigation/parentFlowV1';

const base = {
  candidate_subject: 'con gà con',
  visible_features: ['lông vàng'],
  confidence: 1,
  adult_confirmation_required: true as const,
  decision: 'REVIEW_REQUIRED' as const,
};

describe('FEAT-093 role proposal on the review screen', () => {
  it('starts scenery the adult did not name as unused and keeps the main subject on', () => {
    const candidate: ParentDrawingCandidateV1 = {
      ...base,
      entities: [
        { entity_id: 'main', label: 'con gà con', suggested_role: 'main' },
        { entity_id: 'sec-1', label: 'mặt trời', suggested_role: 'secondary', suggested_included: false },
        { entity_id: 'sec-2', label: 'cái chậu', suggested_role: 'secondary', suggested_included: true },
      ],
    };

    const roles = initialSubjectRoles(candidate);

    expect(roles.map((role) => [role.entity_id, role.role])).toEqual([
      ['main', 'main'],
      ['sec-1', 'excluded'],
      ['sec-2', 'secondary'],
    ]);
  });

  it('follows a proposal that names another object as the main subject', () => {
    const candidate: ParentDrawingCandidateV1 = {
      ...base,
      candidate_subject: 'con mèo',
      entities: [
        { entity_id: 'main', label: 'con mèo', suggested_role: 'secondary' },
        { entity_id: 'sec-1', label: 'con chó', suggested_role: 'main' },
      ],
    };

    const roles = initialSubjectRoles(candidate);

    expect(mainSubjectLabel(roles)).toBe('con chó');
    expect(roles.find((role) => role.entity_id === 'main')?.role).toBe('secondary');
  });

  it('requires a choice only while needs_choice is set and nothing was chosen', () => {
    const ambiguous: ParentDrawingCandidateV1 = { ...base, needs_choice: true };

    expect(mainChoiceRequired(ambiguous, false)).toBe(true);
    expect(mainChoiceRequired(ambiguous, true)).toBe(false);
    expect(mainChoiceRequired(base, false)).toBe(false);
    expect(mainChoiceRequired(null, false)).toBe(false);
  });

  it('reads suggested_included and needs_choice from the server answer', () => {
    const read = readDrawingCandidate({
      ...base,
      needs_choice: true,
      entities: [
        { entity_id: 'main', label: 'con gà con', suggested_role: 'main', suggested_included: true },
        { entity_id: 'sec-1', label: 'cỏ', suggested_role: 'secondary', suggested_included: false },
      ],
    });

    expect(read?.needs_choice).toBe(true);
    expect(read?.entities?.[1].suggested_included).toBe(false);
    expect(readDrawingCandidate({ ...base })?.needs_choice).toBeUndefined();
  });
});
