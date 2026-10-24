import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'
import { sessionService, type Be1Session, type PendingJoinRequest } from '../services/sessionService'
import {
  loadActiveSession,
  saveActiveSession,
  type ActiveSessionRecord,
} from '../services/activeSessionStore'
import type { ManagedProfile } from '../services/profileService'

function withSaved(next: ActiveSessionRecord) {
  saveActiveSession(next)
  return next
}

function applyRoster(current: ActiveSessionRecord, roster: Awaited<ReturnType<typeof sessionService.readRoster>>, revision: number, state: string) {
  const admittedChildren = roster.members.map((member) => ({
    childId: member.child_id,
    displayName: member.display_name,
    membershipId: member.membership_id,
    grantId: member.device_grant_id ?? '',
  }))
  const groups = roster.groups.map((group) => ({
    groupId: group.group_id,
    displayName: group.display_name,
    childIds: roster.members.filter((member) => member.group_id === group.group_id).map((member) => member.child_id),
  }))
  const turns = roster.turns.filter((turn) => turn.state === 'active').map((turn) => ({
    childId: turn.child_id,
    groupId: turn.group_id,
    turnId: turn.turn_id,
  }))
  return withSaved({ ...current, revision: Math.max(revision, roster.session_revision), state, admittedChildren, groups, turns })
}

export function SessionLobbyRuntime() {
  const navigate = useNavigate()
  const [active, setActive] = useState<ActiveSessionRecord | null>(() => loadActiveSession())
  const [session, setSession] = useState<Be1Session | null>(null)
  const [profiles, setProfiles] = useState<ManagedProfile[]>([])
  const [pending, setPending] = useState<PendingJoinRequest[]>([])
  const [selectedProfile, setSelectedProfile] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(() => Boolean(loadActiveSession()))
  const [busyGrant, setBusyGrant] = useState('')
  const [starting, setStarting] = useState(false)
  const [rotatingCode, setRotatingCode] = useState(false)
  const [error, setError] = useState('')

  const refreshPending = useCallback(async (sessionId: string) => {
    const [requests, latest, roster] = await Promise.all([
      sessionService.listJoinRequests(sessionId),
      sessionService.readSession(sessionId),
      sessionService.readRoster(sessionId),
    ])
    setPending(requests)
    setSession(latest)
    const current = loadActiveSession()
    if (current) setActive(applyRoster(current, roster, latest.revision, latest.state))
  }, [])

  useEffect(() => {
    const current = loadActiveSession()
    if (!current) {
      return
    }
    Promise.all([
      sessionService.readSession(current.sessionId),
      sessionService.listProfiles(current.classId),
      sessionService.listJoinRequests(current.sessionId),
      sessionService.readRoster(current.sessionId),
    ]).then(([latest, childProfiles, requests, roster]) => {
      setSession(latest)
      setProfiles(childProfiles)
      setPending(requests)
      const updated = applyRoster(current, roster, latest.revision, latest.state)
      setActive(updated)
    }).catch((cause: unknown) => {
      setError(cause instanceof Error ? cause.message : 'Không tải được trạng thái phòng chờ BE1.')
    }).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const sessionId = active?.sessionId
    if (!sessionId || session?.state !== 'lobby') return
    const timer = window.setInterval(() => {
      void refreshPending(sessionId).catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : 'Không làm mới được yêu cầu tham gia.')
      })
    }, 3000)
    return () => window.clearInterval(timer)
  }, [active?.sessionId, refreshPending, session?.state])

  const inviteUrl = useMemo(() => {
    if (!active?.joinCode) return ''
    const url = new URL('sketch2life://join')
    url.searchParams.set('organizationId', active.organizationId)
    url.searchParams.set('sessionId', active.sessionId)
    url.searchParams.set('joinCode', active.joinCode)
    return url.toString()
  }, [active])

  const admittedIds = new Set(active?.admittedChildren.map((child) => child.childId) ?? [])
  const selectedIds = new Set(Object.values(selectedProfile).filter(Boolean))
  const availableProfiles = (grantId: string) => profiles.filter((profile) =>
    !admittedIds.has(profile.child_id) &&
    (!selectedIds.has(profile.child_id) || selectedProfile[grantId] === profile.child_id),
  )

  const admit = async (request: PendingJoinRequest) => {
    if (!active) return
    const childId = selectedProfile[request.grant_id]
    const profile = profiles.find((item) => item.child_id === childId)
    if (!profile) return
    setBusyGrant(request.grant_id)
    setError('')
    try {
      const receipt = await sessionService.admitDevice(active.sessionId, request.grant_id, childId)
      const updated = withSaved({
        ...active,
        revision: receipt.session_revision,
        admittedChildren: [
          ...active.admittedChildren.filter((child) => child.childId !== childId),
          {
            childId,
            displayName: profile.display_name,
            membershipId: receipt.membership_id,
            grantId: request.grant_id,
          },
        ],
      })
      setActive(updated)
      setPending((items) => items.filter((item) => item.grant_id !== request.grant_id))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'BE1 chưa thể tiếp nhận thiết bị này.')
    } finally {
      setBusyGrant('')
    }
  }

  const reject = async (request: PendingJoinRequest) => {
    if (!active) return
    setBusyGrant(request.grant_id)
    setError('')
    try {
      await sessionService.revokeDevice(active.sessionId, request.grant_id)
      setPending((items) => items.filter((item) => item.grant_id !== request.grant_id))
      await refreshPending(active.sessionId)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'BE1 chưa thể từ chối yêu cầu này.')
    } finally {
      setBusyGrant('')
    }
  }

  const rotateRoomCode = async () => {
    if (!active || session?.state !== 'lobby') return
    setRotatingCode(true)
    setError('')
    try {
      const result = await sessionService.rotateRoomCode(active.sessionId)
      const updated = withSaved({ ...active, roomCode: result.room_code, roomCodeError: undefined })
      setActive(updated)
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : 'Không tạo được mã phòng sáu số.'
      const updated = withSaved({ ...active, roomCode: undefined, roomCodeError: message })
      setActive(updated)
      setError(message)
    } finally {
      setRotatingCode(false)
    }
  }

  const startClass = async () => {
    if (!active || !session || active.admittedChildren.length === 0) return
    setStarting(true)
    setError('')
    try {
      let latest = loadActiveSession() ?? active
      const groupByChild = new Map<string, string>()

      if (latest.drawMode === 'group') {
        let group = latest.groups[0]
        if (!group) {
          const receipt = await sessionService.createGroup(latest.sessionId, 'Nhóm cùng vẽ')
          group = { groupId: receipt.group_id, displayName: receipt.display_name, childIds: [] }
          latest = withSaved({ ...latest, revision: receipt.session_revision, groups: [...latest.groups, group] })
          setActive(latest)
        }
        for (const child of latest.admittedChildren) groupByChild.set(child.childId, group.groupId)
      } else {
        for (const child of latest.admittedChildren) {
          let group = latest.groups.find((item) => item.childIds.includes(child.childId))
          if (!group) {
            const receipt = await sessionService.createGroup(latest.sessionId, `Bức vẽ ${child.displayName}`)
            group = { groupId: receipt.group_id, displayName: receipt.display_name, childIds: [] }
            latest = withSaved({ ...latest, revision: receipt.session_revision, groups: [...latest.groups, group] })
            setActive(latest)
          }
          groupByChild.set(child.childId, group.groupId)
        }
      }

      for (const child of latest.admittedChildren) {
        const groupId = groupByChild.get(child.childId)
        if (!groupId) throw new Error(`Chưa có nhóm cho ${child.displayName}.`)
        const group = latest.groups.find((item) => item.groupId === groupId)
        if (!group?.childIds.includes(child.childId)) {
          const assignment = await sessionService.assignMember(latest.sessionId, groupId, child.childId, latest.revision)
          latest = withSaved({
            ...latest,
            revision: assignment.session_revision,
            groups: latest.groups.map((item) => item.groupId === groupId
              ? { ...item, childIds: [...new Set([...item.childIds, child.childId])] }
              : item),
          })
          setActive(latest)
        }
      }

      if (latest.state === 'lobby') {
        const started = await sessionService.startSession(latest.sessionId, latest.revision)
        latest = withSaved({ ...latest, revision: started.revision, state: started.state, joinCode: undefined, roomCode: undefined })
        setActive(latest)
        setSession(started)
        setPending([])
      }

      const groupsToTurn = latest.drawMode === 'group'
        ? latest.groups.slice(0, 1).map((group) => ({ group, child: latest.admittedChildren[0] })).filter((entry) => entry.child)
        : latest.admittedChildren.map((child) => ({
            group: latest.groups.find((item) => item.childIds.includes(child.childId)),
            child,
          })).filter((entry) => entry.group)

      for (const entry of groupsToTurn) {
        if (!entry.group || latest.turns.some((turn) => turn.groupId === entry.group?.groupId && turn.childId === entry.child.childId)) continue
        const receipt = await sessionService.startChildTurn(latest.sessionId, entry.group.groupId, entry.child.childId)
        latest = withSaved({ ...latest, turns: [...latest.turns.filter((turn) => turn.groupId !== entry.group?.groupId), {
          childId: entry.child.childId,
          groupId: entry.group.groupId,
          turnId: receipt.turn_id,
        }] })
        setActive(latest)
      }
      navigate('/session/orchestrate')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không thể bắt đầu phiên BE1.')
    } finally {
      setStarting(false)
    }
  }

  if (loading) return <main className="p-8 text-slate-600">Đang tải phòng chờ từ BE1…</main>
  if (!active) return <main className="m-7 rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-900">{error || 'Không có phiên BE1 đang mở. Hãy tạo phiên từ trang Thiết lập phiên học.'}</main>

  return (
    <main className="mx-auto max-w-6xl space-y-5 px-7 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-blue-700">Phòng chờ BE1 · {session?.state ?? active.state}</p>
          <h1 className="mt-1 text-3xl font-extrabold text-slate-900">{active.title}</h1>
          <p className="mt-2 text-sm text-slate-600">Session {active.sessionId} · Lớp {active.classId} · Chế độ {active.drawMode === 'group' ? 'cùng vẽ' : 'cá nhân'}</p>
        </div>
        {session?.state === 'active'
          ? <button onClick={() => navigate('/session/orchestrate')} className="rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white">Mở điều phối lớp</button>
          : <button disabled={starting || active.admittedChildren.length === 0} onClick={() => void startClass()} className="rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">{starting ? 'Đang phân nhóm và bắt đầu…' : 'Bắt đầu lớp'}</button>}
      </header>

      {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</div>}

      {session?.state === 'lobby' && <section className="grid gap-5 lg:grid-cols-[260px_1fr]">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 text-center">
          <h2 className="font-bold text-slate-900">Quét để yêu cầu tham gia</h2>
          {inviteUrl ? <QRCodeSVG className="mx-auto my-4 h-auto w-full max-w-52" value={inviteUrl} level="M" /> : <p className="my-6 text-sm text-rose-700">BE1 không trả join code; QR chưa thể tạo.</p>}
          <p className="text-xs text-slate-500">QR mở ứng dụng Child và gửi yêu cầu chờ duyệt. Sau khi bắt đầu, BE1 từ chối yêu cầu mới.</p>
          <div className="mt-4 rounded-xl border border-blue-100 bg-blue-50 p-4 text-left">
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-800">Mã phòng dùng chung</p>
            {active.roomCode
              ? <p className="my-2 text-4xl font-black tracking-[0.3em] text-slate-900" aria-label="Mã phòng sáu số">{active.roomCode}</p>
              : <p className="my-2 text-sm text-amber-900">{active.roomCodeError || 'Đang chờ cấu hình khoá bảo mật BE1.'}</p>}
            <button disabled={rotatingCode || session?.state !== 'lobby'} onClick={() => void rotateRoomCode()} className="rounded-lg border border-blue-300 bg-white px-3 py-2 text-sm font-semibold text-blue-800 disabled:opacity-50">{rotatingCode ? 'Đang đổi mã…' : active.roomCode ? 'Đổi mã trước khi bắt đầu' : 'Tạo mã phòng'}</button>
          </div>
        </div>

        <div className="space-y-5">
          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-lg font-bold text-slate-900">Yêu cầu đang chờ ({pending.length})</h2>
              <button onClick={() => void refreshPending(active.sessionId)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700">Làm mới</button>
            </div>
            {pending.length === 0 ? <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">Chưa có thiết bị gửi yêu cầu.</p> : <ul className="divide-y divide-slate-100">
              {pending.map((request) => <li key={request.grant_id} className="flex flex-wrap items-center gap-3 py-4">
                <div className="min-w-0 flex-1"><p className="font-semibold text-slate-800">Thiết bị chờ xác nhận</p><p className="text-xs text-slate-500">{request.requested_at ? new Date(request.requested_at).toLocaleString() : 'Thời gian chưa có'}</p></div>
                <select aria-label={`Chọn hồ sơ cho ${request.grant_id}`} value={selectedProfile[request.grant_id] ?? ''} onChange={(event) => setSelectedProfile((value) => ({ ...value, [request.grant_id]: event.target.value }))} className="min-w-48 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm">
                  <option value="">Chọn hồ sơ sau khi xác nhận trẻ</option>
                  {availableProfiles(request.grant_id).map((profile) => <option key={profile.child_id} value={profile.child_id}>{profile.display_name}</option>)}
                </select>
                <button disabled={busyGrant === request.grant_id || !selectedProfile[request.grant_id]} onClick={() => void admit(request)} className="rounded-lg bg-blue-700 px-4 py-2 font-semibold text-white disabled:opacity-50">{busyGrant === request.grant_id ? 'Đang xử lý…' : 'Tiếp nhận'}</button>
                <button disabled={busyGrant === request.grant_id} onClick={() => void reject(request)} className="rounded-lg border border-slate-300 px-4 py-2 font-semibold text-slate-700 disabled:opacity-50">Từ chối</button>
              </li>)}
            </ul>}
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            <h2 className="mb-3 text-lg font-bold text-slate-900">Đã được BE1 tiếp nhận ({active.admittedChildren.length})</h2>
            {active.admittedChildren.length === 0 ? <p className="text-sm text-slate-600">Chọn hồ sơ và tiếp nhận thiết bị. BE1 sẽ kiểm tra lại consent trước khi cho bắt đầu.</p> : <ul className="grid gap-2 sm:grid-cols-2">{active.admittedChildren.map((child) => <li key={child.childId} className="rounded-xl bg-emerald-50 px-4 py-3 text-sm font-semibold text-emerald-900">{child.displayName}<span className="ml-2 text-xs font-normal text-emerald-700">membership đã lưu</span></li>)}</ul>}
            <p className="mt-4 rounded-xl bg-slate-50 p-3 text-xs text-slate-600">Danh sách lớp, hồ sơ được ghép và nhóm được tải lại từ roster BE1 mỗi lần mở hoặc làm mới phòng chờ.</p>
          </section>
        </div>
      </section>}

      {session?.state !== 'lobby' && session?.state !== 'active' && <p className="rounded-xl bg-amber-50 p-4 text-sm text-amber-900">Phiên đang ở trạng thái {session?.state ?? 'chưa đọc được'}. BE1 chỉ nhận yêu cầu tham gia khi phòng chờ đang mở.</p>}
    </main>
  )
}
