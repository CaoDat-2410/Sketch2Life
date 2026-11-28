import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { ParentApplicationError } from '../src/parent/application/ParentApplicationError';
import { safeParentFlowErrorMessage, safeProfileFieldMessages } from '../src/parent/presentation/navigation/parentFlowV1';
import {
  clearSensitiveSupportNeedsState,
  supportNeedsPutInput,
  supportNeedsFieldMessage,
  supportNeedsStateForLoadFailure,
  SUPPORT_NEEDS_UNAVAILABLE_MESSAGE,
} from '../src/parent/presentation/screens/supportNeedsScreenState';

describe('Parent Phase B support-needs privacy states', () => {
  it('shows the calm unavailable copy for the production 503 response', () => {
    const error = new ParentApplicationError('SUPPORT_NEEDS_UNAVAILABLE', 'safe', 'request-01', 503);
    const state = supportNeedsStateForLoadFailure(error);

    expect(state).toEqual({ status: 'unavailable', message: SUPPORT_NEEDS_UNAVAILABLE_MESSAGE });
    expect(safeParentFlowErrorMessage(error)).toBe(SUPPORT_NEEDS_UNAVAILABLE_MESSAGE);
  });

  it('keeps support-needs text exactly as entered in the required nullable fields', () => {
    expect(supportNeedsPutInput(0, '  support detail  ', '')).toEqual({
      expected_revision: 0, category: '  support detail  ', note: '',
    });
  });

  it('clears editor values when leaving the screen', () => {
    const privateText = 'sensitive test detail';
    const current = {
      status: 'value' as const,
      revision: 4,
      category: privateText,
      note: privateText,
      fieldErrors: {},
      notice: '',
    };
    const cleared = clearSensitiveSupportNeedsState(current);
    const screenSource = readFileSync(new URL('../src/parent/presentation/screens/SupportNeedsScreen.tsx', import.meta.url), 'utf8');

    expect(cleared).toEqual({ status: 'loading' });
    expect(JSON.stringify(cleared)).not.toContain(privateText);
    expect(screenSource).toContain('updateState(clearSensitiveSupportNeedsState(stateRef.current));');
    expect(screenSource).toContain('stateRef.current = clearSensitiveSupportNeedsState(stateRef.current);');
    expect(screenSource).not.toMatch(/console\.(log|warn|error)/u);
  });

  it('maps diagnosis-like field errors to safe copy without echoing field text', () => {
    const privateText = 'sensitive diagnosis-like text';
    const error = new ParentApplicationError('INVALID_REQUEST', 'generic', 'request-02', 400, {
      fieldErrors: [{ field: 'interests_summary', code: 'DIAGNOSIS_LIKE' }],
    });
    const profileField = safeProfileFieldMessages(error).interests_summary ?? '';
    const supportField = supportNeedsFieldMessage('DIAGNOSIS_LIKE');

    expect(profileField).toBe('Nội dung không nên nêu chẩn đoán.');
    expect(supportField).toBe(profileField);
    expect(`${profileField} ${supportField} ${safeParentFlowErrorMessage(error)}`).not.toContain(privateText);
    expect(`${profileField} ${supportField}`).not.toContain('DIAGNOSIS_LIKE');
  });
});
