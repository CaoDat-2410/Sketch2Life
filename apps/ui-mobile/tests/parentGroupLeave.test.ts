import { readFileSync } from 'node:fs';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://parent.example.test' },
}));

import { ParentLessonUseCases } from '../src/parent/application/use-cases/ParentLessonUseCases';
import type { ParentApiPort } from '../src/parent/application/ports/ParentPorts';
import type { ParentGroupMembershipV1 } from '../src/parent/domain/types';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';
import {
  canLeaveParentGroupMembership,
  parentGroupLeaveActionKey,
  retainedParentGroupLeaveActionIdentity,
  type ParentGroupLeaveActionIdentity,
} from '../src/parent/presentation/navigation/workflowTypes';
import { safeParentGroupMembershipErrorMessage } from '../src/parent/presentation/navigation/parentFlowV1';

type Call = { url: string; init: RequestInit };

function reply(status: number, body: unknown = {}, headers: Record<string, string> = {}): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(headers),
    json: async () => body,
    body: { cancel: async () => undefined },
  } as unknown as Response;
}

function apiWith(replies: Response[]) {
  const calls: Call[] = [];
  const queue = [...replies];
  const fetcher = vi.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    return queue.shift() ?? reply(200);
  }) as unknown as typeof fetch;
  const api = new ParentApi({ getIdToken: vi.fn(async () => 'parent-token') }, fetcher, 'https://parent.example.test');
  return { api, calls };
}

function headerOf(call: Call, name: string): string | null {
  return new Headers(call.init.headers).get(name);
}

function activeMembership(overrides: Partial<ParentGroupMembershipV1> = {}): ParentGroupMembershipV1 {
  return {
    contract: 'ParentGroupMembershipV1',
    membership_id: 'member/one',
    parent_group_id: 'group one',
    organization_id: 'org/one',
    state: 'ACTIVE',
    invited_at: '2026-11-20T10:00:00Z',
    expires_at: null,
    accepted_at: '2026-11-21T10:00:00Z',
    revision: 7,
    revision_source: 'PARENT_ACTION',
    ...overrides,
  };
}

describe('parent self-revoke from group', () => {
  it('DELETEs the encoded organization path with quoted revision and idempotency headers, then parses REVOKED', async () => {
    const revoked = activeMembership({ state: 'REVOKED', revision: 8, revision_source: 'PARENT_LEFT' });
    const { api, calls } = apiWith([reply(200, revoked, { ETag: '"8"' })]);

    const result = await api.leaveParentGroup('org/one', 'group one', 'member/one', 7, 'leave-key-1');

    expect(result).toMatchObject({ membership_id: 'member/one', state: 'REVOKED', revision: 8 });
    expect(calls[0].url).toBe('https://parent.example.test/api/lesson-library/v1/organizations/org%2Fone/parent-groups/group%20one/members/member%2Fone');
    expect(calls[0].init.method).toBe('DELETE');
    expect(headerOf(calls[0], 'If-Match')).toBe('"7"');
    expect(headerOf(calls[0], 'Idempotency-Key')).toBe('leave-key-1');
    expect(headerOf(calls[0], 'Content-Type')).toBeNull();
    expect(calls[0].init.body).toBeUndefined();
  });

  it('passes the same leave action identity through the lesson use case', async () => {
    const revoked = activeMembership({ state: 'REVOKED', revision: 8 });
    const leave = vi.fn(async () => revoked);
    const useCases = new ParentLessonUseCases({ leaveParentGroup: leave } as unknown as ParentApiPort);

    await useCases.leaveGroup('org/one', 'group one', 'member/one', 7, 'same-key-on-retry');

    expect(leave).toHaveBeenCalledWith('org/one', 'group one', 'member/one', 7, 'same-key-on-retry');
  });

  it('keeps the stale current_version so the controller can reload memberships', async () => {
    const { api } = apiWith([reply(409, { code: 'STALE_REVISION', current_version: 9 })]);
    const error = await api.leaveParentGroup('org/one', 'group one', 'member/one', 7, 'leave-key-1')
      .catch((cause: unknown) => cause);

    expect(error).toMatchObject({ code: 'STALE_REVISION', status: 409, currentVersion: 9 });
  });

  it('reuses one key for the same membership revision and creates a new key after stale or revised state', () => {
    const actions = new Map<string, ParentGroupLeaveActionIdentity>();
    const createIdentity = vi.fn()
      .mockReturnValueOnce('leave-key-1')
      .mockReturnValueOnce('leave-key-2')
      .mockReturnValueOnce('leave-key-3');
    const membership = activeMembership();

    expect(retainedParentGroupLeaveActionIdentity(actions, membership, createIdentity)).toBe('leave-key-1');
    expect(retainedParentGroupLeaveActionIdentity(actions, membership, createIdentity)).toBe('leave-key-1');
    expect(createIdentity).toHaveBeenCalledTimes(1);

    actions.delete(parentGroupLeaveActionKey(membership));
    expect(retainedParentGroupLeaveActionIdentity(actions, membership, createIdentity)).toBe('leave-key-2');
    expect(retainedParentGroupLeaveActionIdentity(actions, { ...membership, revision: 8 }, createIdentity)).toBe('leave-key-3');
  });

  it('shows leave only for ACTIVE memberships with an organization id', () => {
    expect(canLeaveParentGroupMembership(activeMembership())).toBe(true);
    expect(canLeaveParentGroupMembership(activeMembership({ organization_id: undefined }))).toBe(false);
    expect(canLeaveParentGroupMembership(activeMembership({ organization_id: '  ' }))).toBe(false);
    expect(canLeaveParentGroupMembership(activeMembership({ state: 'REVOKED' }))).toBe(false);
  });

  it('reloads lessons and memberships for stale or already-revoked answers', () => {
    const controller = readFileSync(new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url), 'utf8');
    const leaveGroup = controller.match(/async function leaveGroup\(membership: ParentGroupMembershipV1\)[\s\S]*?\n  async function respondToInvitation/)?.[0] ?? '';

    expect(leaveGroup).toContain("code === 'STALE_REVISION' || code === 'INVALID_STATE_TRANSITION'");
    expect(leaveGroup).toContain("await openLessons('gallery')");
    expect(leaveGroup).toContain('groupLeaveActionIdentities.current.delete(actionKey)');
  });

  it('asks for confirmation with the access-loss and reinvitation copy', () => {
    const screen = readFileSync(new URL('../src/parent/presentation/screens/LessonGalleryScreen.tsx', import.meta.url), 'utf8');

    expect(screen).toContain('Alert.alert(');
    expect(screen).toContain('Bạn sẽ mất quyền truy cập các bài học được chia sẻ qua nhóm này.');
    expect(screen).toContain('Nhà trường có thể mời bạn tham gia lại sau.');
    expect(screen).toContain("text: 'Rời nhóm'");
    expect(screen).toContain('onPress: onConfirm');
    expect(screen).toContain('canLeaveParentGroupMembership(membership)');
    expect(screen).toContain('disabled={Boolean(props.loadingId)}');
  });

  it('shows safe Vietnamese messages without server error codes', () => {
    const cases = [
      ['STALE_REVISION', 409, 'Dữ liệu nhóm đã thay đổi, hãy xem lại rồi xác nhận lại.'],
      ['INVALID_STATE_TRANSITION', 409, 'Nhóm này đã được rời hoặc thu hồi. Danh sách đã được tải lại.'],
      ['RESOURCE_NOT_FOUND', 404, 'Không tìm thấy nhóm hoặc bạn không thể truy cập nhóm này.'],
      ['PROVIDER_UNAVAILABLE', 503, 'Dịch vụ nhóm tạm thời không khả dụng. Hãy thử lại sau.'],
    ] as const;
    for (const [code, status, expected] of cases) {
      const message = safeParentGroupMembershipErrorMessage(new ParentApiError(code, 'request-1', status));
      expect(message).toBe(expected);
      expect(message).not.toContain(code);
    }
  });
});
