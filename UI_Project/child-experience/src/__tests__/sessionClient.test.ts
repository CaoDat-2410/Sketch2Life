import { childApiFetch, saveDeviceContext } from '../services/apiClient'
import { appendStroke, requestDeviceJoin, requestRoomCodeJoin, waitForAdmissionAndTurn } from '../services/sessionClient'

jest.mock('../services/apiClient', () => ({
  ChildApiError: class ChildApiError extends Error {
    readonly status: number
    readonly code: string

    constructor(message: string, status: number, code: string) {
      super(message)
      this.status = status
      this.code = code
    }
  },
  childApiFetch: jest.fn(),
  newDeviceKey: () => 'device-key-test',
  saveDeviceContext: jest.fn().mockResolvedValue(undefined),
}))

describe('requestDeviceJoin', () => {
  beforeEach(() => jest.clearAllMocks())

  it('sends the QR invite to BE1 and saves the pending device grant', async () => {
    ;(childApiFetch as jest.Mock).mockResolvedValue({
      contract: 'Be1DeviceJoinV1',
      grant_id: 'grant-test',
      state: 'pending',
      session_revision: 2,
    })

    const context = await requestDeviceJoin({
      organizationId: 'org-test',
      sessionId: 'session-test',
      joinCode: 'invite-code-123',
    })

    expect(childApiFetch).toHaveBeenCalledWith(
      '/organizations/org-test/sessions/session-test/join',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(context).toEqual({
      organizationId: 'org-test',
      sessionId: 'session-test',
      grantId: 'grant-test',
      deviceKey: 'device-key-test',
    })
    expect(saveDeviceContext).toHaveBeenCalledWith(context)
  })

  it('rejects malformed QR credentials before making a backend request', async () => {
    await expect(requestDeviceJoin({
      organizationId: 'org-test',
      sessionId: 'session-test',
      joinCode: '123456',
    })).rejects.toThrow('Liên kết mời không hợp lệ.')

    expect(childApiFetch).not.toHaveBeenCalled()
  })

  it('uses one stable idempotency key for a durable canvas stroke write', async () => {
    const context = {
      organizationId: 'org-test',
      sessionId: 'session-test',
      grantId: 'grant-test',
      deviceKey: 'device-key-test',
    }
    const canvas = { turn_id: 'turn-test', document_epoch: 1, current_revision: 7 }
    const stroke = { points: [{ x: 0.1, y: 0.2 }, { x: 0.3, y: 0.4 }], color: '#1685F8', size: 9 }
    ;(childApiFetch as jest.Mock).mockResolvedValue({ resulting_revision: 8, operation_id: 'operation-test' })

    await appendStroke(context, canvas, stroke, 'operation-test')

    expect(childApiFetch).toHaveBeenCalledWith(
      '/organizations/org-test/sessions/session-test/canvas/operations',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Idempotency-Key': 'operation-test' },
        body: JSON.stringify({
          operation_id: 'operation-test',
          turn_id: 'turn-test',
          document_epoch: 1,
          expected_revision: 7,
          operation_payload: { kind: 'stroke', ...stroke },
        }),
      }),
      context,
    )
  })

  it('loads reconnect operation pages until the current canvas revision is covered', async () => {
    const context = {
      organizationId: 'org-test',
      sessionId: 'session-test',
      grantId: 'grant-test',
      deviceKey: 'device-key-test',
    }
    const firstPage = Array.from({ length: 500 }, (_, index) => ({
      operation_id: `operation-${index + 1}`,
      resulting_revision: index + 1,
      operation_payload: { kind: 'stroke' },
    }))
    const finalPage = [{ operation_id: 'operation-501', resulting_revision: 501, operation_payload: { kind: 'stroke' } }]
    ;(childApiFetch as jest.Mock)
      .mockResolvedValueOnce({ contract: 'Be1DeviceGrantRefreshV1', grant_id: 'grant-test', state: 'admitted', device_key: 'rotated-device-key' })
      .mockResolvedValueOnce({
        contract: 'Be1CanvasReconnectV1', canvas_id: 'group-test', turn_id: 'turn-test',
        document_epoch: 1, current_revision: 501, checkpoint: null, operations: firstPage,
      })
      .mockResolvedValueOnce({
        contract: 'Be1CanvasReconnectV1', canvas_id: 'group-test', turn_id: 'turn-test',
        document_epoch: 1, current_revision: 501, checkpoint: null, operations: finalPage,
      })

    const result = await waitForAdmissionAndTurn(context, () => undefined, new AbortController().signal)

    expect(result?.canvas.operations).toHaveLength(501)
    expect(childApiFetch).toHaveBeenNthCalledWith(
      3,
      '/organizations/org-test/sessions/session-test/reconnect?after_revision=500',
      {},
      { ...context, deviceKey: 'rotated-device-key' },
    )
  })
})

describe('requestRoomCodeJoin', () => {
  beforeEach(() => jest.clearAllMocks())

  it('sends the shared six-digit room code and saves an opaque pending grant', async () => {
    ;(childApiFetch as jest.Mock).mockResolvedValue({
      contract: 'Be1DeviceJoinV1', grant_id: 'grant-room', state: 'pending', session_revision: 4,
    })
    const context = await requestRoomCodeJoin('004206')
    expect(childApiFetch).toHaveBeenCalledWith('/room-code/join', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ room_code: '004206', device_key: 'device-key-test' }),
    }))
    expect(context).toEqual({ organizationId: '', sessionId: '', grantId: 'grant-room', deviceKey: 'device-key-test' })
    expect(saveDeviceContext).toHaveBeenCalledWith(context)
  })

  it('rejects malformed codes before making a backend request', async () => {
    await expect(requestRoomCodeJoin('4206')).rejects.toThrow('Mã phòng gồm sáu chữ số.')
    expect(childApiFetch).not.toHaveBeenCalled()
  })
})

describe('room-code admission polling', () => {
  beforeEach(() => jest.clearAllMocks())

  it('reveals class scope only after admission and then uses the device-grant contract', async () => {
    const context = { organizationId: '', sessionId: '', grantId: 'grant-room', deviceKey: 'device-key-test' }
    ;(childApiFetch as jest.Mock)
      .mockResolvedValueOnce({
        contract: 'Be1DeviceJoinStatusV1', grant_id: 'grant-room', state: 'admitted',
        organization_id: 'org-room', session_id: 'session-room',
      })
      .mockResolvedValueOnce({
        contract: 'Be1DeviceGrantRefreshV1', grant_id: 'grant-room', state: 'admitted',
        device_key: 'rotated-room-key',
      })
      .mockResolvedValueOnce({
        contract: 'Be1CanvasReconnectV1', canvas_id: 'canvas-room', turn_id: 'turn-room',
        document_epoch: 1, current_revision: 0, checkpoint: null, operations: [],
      })

    const result = await waitForAdmissionAndTurn(context, () => undefined, new AbortController().signal)
    expect(result?.context).toEqual({
      organizationId: 'org-room', sessionId: 'session-room', grantId: 'grant-room', deviceKey: 'rotated-room-key',
    })
    expect(childApiFetch).toHaveBeenNthCalledWith(
      1, '/device-grants/grant-room/join-status', { method: 'POST' }, context,
    )
    expect(childApiFetch).toHaveBeenNthCalledWith(
      2,
      '/organizations/org-room/sessions/session-room/device-grants/grant-room/refresh',
      { method: 'POST' },
      { ...context, organizationId: 'org-room', sessionId: 'session-room' },
    )
  })
})
