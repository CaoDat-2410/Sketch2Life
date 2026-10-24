import {
  ChildApiError,
  childApiFetch,
  newDeviceKey,
  saveDeviceContext,
  type ChildDeviceContext,
} from './apiClient'

interface JoinReceipt {
  contract: 'Be1DeviceJoinV1'
  grant_id: string
  state: 'pending' | 'admitted'
  session_revision: number
}

interface GrantRefresh {
  contract: 'Be1DeviceGrantRefreshV1'
  grant_id: string
  state: 'pending' | 'admitted' | 'revoked'
  device_key?: string
}

interface JoinStatus {
  contract: 'Be1DeviceJoinStatusV1'
  grant_id: string
  state: 'pending' | 'admitted' | 'revoked'
  organization_id?: string
  session_id?: string
}

export interface CanvasReconnect {
  contract: 'Be1CanvasReconnectV1'
  canvas_id: string
  turn_id: string
  document_epoch: number
  current_revision: number
  checkpoint: { snapshot: Record<string, unknown> } | null
  operations: Array<{ operation_id: string; resulting_revision: number; operation_payload: Record<string, unknown> }>
}

export interface JoinInvite {
  organizationId: string
  sessionId: string
  joinCode: string
}

export function newCanvasOperationId() {
  return newDeviceKey()
}

function pause(ms: number, signal: AbortSignal) {
  return new Promise<void>((resolve) => {
    const timer = setTimeout(resolve, ms)
    signal.addEventListener('abort', () => { clearTimeout(timer); resolve() }, { once: true })
  })
}

export async function requestDeviceJoin(invite: JoinInvite): Promise<ChildDeviceContext> {
  if (!/^[A-Za-z0-9_-]{8,32}$/.test(invite.joinCode)) throw new Error('Liên kết mời không hợp lệ.')
  const deviceKey = newDeviceKey()
  const receipt = await childApiFetch<JoinReceipt>(
    `/organizations/${encodeURIComponent(invite.organizationId)}/sessions/${encodeURIComponent(invite.sessionId)}/join`,
    {
      method: 'POST',
      body: JSON.stringify({ join_code: invite.joinCode, device_key: deviceKey }),
    },
  )
  const context: ChildDeviceContext = {
    organizationId: invite.organizationId,
    sessionId: invite.sessionId,
    grantId: receipt.grant_id,
    deviceKey,
  }
  await saveDeviceContext(context)
  return context
}

export async function requestRoomCodeJoin(roomCode: string): Promise<ChildDeviceContext> {
  if (!/^\d{6}$/.test(roomCode)) throw new Error('Mã phòng gồm sáu chữ số.')
  const deviceKey = newDeviceKey()
  const receipt = await childApiFetch<JoinReceipt>('/room-code/join', {
    method: 'POST',
    body: JSON.stringify({ room_code: roomCode, device_key: deviceKey }),
  })
  const context: ChildDeviceContext = {
    organizationId: '',
    sessionId: '',
    grantId: receipt.grant_id,
    deviceKey,
  }
  await saveDeviceContext(context)
  return context
}

async function loadCompleteCanvas(context: ChildDeviceContext): Promise<CanvasReconnect> {
  const basePath = `/organizations/${encodeURIComponent(context.organizationId)}/sessions/${encodeURIComponent(context.sessionId)}/reconnect`
  const result = await childApiFetch<CanvasReconnect>(basePath, {}, context)
  const operations = [...result.operations]
  let afterRevision = operations.at(-1)?.resulting_revision ?? 0
  while (operations.length >= 500 && afterRevision < result.current_revision) {
    const page = await childApiFetch<CanvasReconnect>(
      `${basePath}?after_revision=${afterRevision}`,
      {},
      context,
    )
    if (page.operations.length === 0) break
    operations.push(...page.operations)
    const nextRevision = page.operations.at(-1)?.resulting_revision ?? afterRevision
    if (nextRevision <= afterRevision) break
    afterRevision = nextRevision
  }
  return { ...result, operations }
}

export async function waitForAdmissionAndTurn(
  initial: ChildDeviceContext,
  onStatus: (status: 'waiting' | 'admitted' | 'ready') => void,
  signal: AbortSignal,
): Promise<{ context: ChildDeviceContext; canvas: CanvasReconnect } | null> {
  let context = initial
  onStatus('waiting')
  while (!signal.aborted) {
    if (!context.organizationId || !context.sessionId) {
      const joined = await childApiFetch<JoinStatus>(
        `/device-grants/${encodeURIComponent(context.grantId)}/join-status`,
        { method: 'POST' },
        context,
      )
      if (joined.state === 'revoked') {
        throw new Error('Yêu cầu tham gia đã bị thu hồi. Hãy nhờ cô/thầy hỗ trợ.')
      }
      if (joined.state !== 'admitted') {
        await pause(4_000, signal)
        continue
      }
      if (!joined.organization_id || !joined.session_id) {
        throw new Error('BE1 không trả phạm vi lớp sau khi tiếp nhận thiết bị.')
      }
      context = { ...context, organizationId: joined.organization_id, sessionId: joined.session_id }
      await saveDeviceContext(context)
    }
    const path = `/organizations/${encodeURIComponent(context.organizationId)}/sessions/${encodeURIComponent(context.sessionId)}/device-grants/${encodeURIComponent(context.grantId)}/refresh`
    let refreshed: GrantRefresh
    try {
      refreshed = await childApiFetch<GrantRefresh>(path, { method: 'POST' }, context)
    } catch (cause) {
      if (cause instanceof ChildApiError && cause.code === 'INVALID_DEVICE_CREDENTIAL') {
        await pause(4_000, signal)
        continue
      }
      throw cause
    }
    if (refreshed.state === 'revoked') throw new Error('Yêu cầu tham gia đã bị thu hồi. Hãy nhờ cô/thầy hỗ trợ.')
    if (refreshed.state === 'pending') {
      await pause(4_000, signal)
      continue
    }
    if (!refreshed.device_key) throw new Error('BE1 không cấp lại được thông tin thiết bị.')
    context = { ...context, deviceKey: refreshed.device_key }
    await saveDeviceContext(context)
    onStatus('admitted')

    while (!signal.aborted) {
      try {
        const canvas = await loadCompleteCanvas(context)
        onStatus('ready')
        return { context, canvas }
      } catch (cause) {
        if (cause instanceof ChildApiError && [
          'DEVICE_SCOPE_INACTIVE',
          'DEVICE_MEMBERSHIP_INACTIVE',
          'GROUP_NOT_WRITABLE',
          'ACTIVE_TURN_REQUIRED',
        ].includes(cause.code)) {
          await pause(4_000, signal)
          continue
        }
        throw cause
      }
    }
  }
  return null
}

export async function appendStroke(
  context: ChildDeviceContext,
  canvas: Pick<CanvasReconnect, 'turn_id' | 'document_epoch' | 'current_revision'>,
  stroke: { points: Array<{ x: number; y: number }>; color: string; size: number },
  operationId = newCanvasOperationId(),
) {
  const organization = encodeURIComponent(context.organizationId)
  const session = encodeURIComponent(context.sessionId)
  return childApiFetch<{ resulting_revision: number; operation_id: string }>(
    `/organizations/${organization}/sessions/${session}/canvas/operations`,
    {
      method: 'POST',
      headers: { 'Idempotency-Key': operationId },
      body: JSON.stringify({
        operation_id: operationId,
        turn_id: canvas.turn_id,
        document_epoch: canvas.document_epoch,
        expected_revision: canvas.current_revision,
        operation_payload: { kind: 'stroke', ...stroke },
      }),
    },
    context,
  )
}
