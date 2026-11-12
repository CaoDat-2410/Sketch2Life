import { useEffect, useState } from 'react'
import { sessionService, type Be1LearningStage, type Be1Roster, type Be1Session, type Be1StageState } from '../services/sessionService'
import { loadActiveSession, saveActiveSession, type ActiveSessionRecord } from '../services/activeSessionStore'

export function SessionOrchestrateRuntime() {
  const [active, setActive] = useState<ActiveSessionRecord | null>(() => loadActiveSession())
  const [session, setSession] = useState<Be1Session | null>(null)
  const [stage, setStage] = useState<Be1StageState | null>(null)
  const [roster, setRoster] = useState<Be1Roster | null>(null)
  const [outcome, setOutcome] = useState<string | null>(null)
  const [earlyReason, setEarlyReason] = useState<'time' | 'safety' | 'technical' | 'other'>('time')
  const [teacherNote, setTeacherNote] = useState('')
  const [draftAcknowledged, setDraftAcknowledged] = useState(false)
  const [assistanceNotNeeded, setAssistanceNotNeeded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    const current = loadActiveSession()
    if (!current) return
    Promise.all([
      sessionService.readSession(current.sessionId),
      sessionService.readRoster(current.sessionId),
      sessionService.readLearningStage(current.sessionId),
      sessionService.readOutcome(current.sessionId),
    ]).then(([latest, latestRoster, latestStage, latestOutcome]) => {
      setSession(latest)
      setRoster(latestRoster)
      setStage(latestStage)
      setOutcome(latestOutcome.outcome?.value ?? null)
      const admittedChildren = latestRoster.members.map((member) => ({
        childId: member.child_id,
        displayName: member.display_name,
        membershipId: member.membership_id,
        grantId: member.device_grant_id ?? '',
      }))
      const groups = latestRoster.groups.map((group) => ({
        groupId: group.group_id,
        displayName: group.display_name,
        childIds: latestRoster.members.filter((member) => member.group_id === group.group_id).map((member) => member.child_id),
      }))
      const turns = latestRoster.turns.filter((turn) => turn.state === 'active').map((turn) => ({
        childId: turn.child_id,
        groupId: turn.group_id,
        turnId: turn.turn_id,
      }))
      const updated = { ...current, revision: latest.revision, state: latest.state, admittedChildren, groups, turns }
      saveActiveSession(updated)
      setActive(updated)
    }).catch((cause: unknown) => setError(cause instanceof Error ? cause.message : 'Không tải được trạng thái phiên BE1.'))
  }, [])

  const transition = async (action: 'pause' | 'resume') => {
    if (!active || !session) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const updatedSession = action === 'pause'
        ? await sessionService.pauseSession(active.sessionId, session.revision)
        : await sessionService.resumeSession(active.sessionId, session.revision)
      const updated = { ...active, state: updatedSession.state, revision: updatedSession.revision }
      saveActiveSession(updated)
      setActive(updated)
      setSession(updatedSession)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : `Không thể ${action === 'pause' ? 'tạm dừng' : 'tiếp tục'} phiên.`)
    } finally {
      setBusy(false)
    }
  }

  const stageOrder: Be1LearningStage[] = [
    'preparation', 'join', 'explore_draw', 'assistance', 'sharing',
    'knowledge', 'off_screen', 'reflection', 'completion',
  ]
  const stageLabels: Record<Be1LearningStage, string> = {
    preparation: 'Chuẩn bị', join: 'Tham gia lớp', explore_draw: 'Khám phá và vẽ',
    assistance: 'Hỗ trợ linh hoạt', sharing: 'Chia sẻ tác phẩm', knowledge: 'Khám phá kiến thức',
    off_screen: 'Hoạt động ngoài màn hình', reflection: 'Suy ngẫm và đánh giá', completion: 'Hoàn tất',
  }
  const currentStageIndex = stage ? stageOrder.indexOf(stage.stage) : -1
  const nextStage = currentStageIndex >= 0 ? stageOrder[currentStageIndex + 1] : undefined
  const unfinishedGroups = roster?.groups.filter((group) =>
    ['active', 'locked'].includes(group.state)
      && roster.members.some((member) => member.group_id === group.group_id && member.progress !== 'completed'),
  ) ?? []
  const unfinishedGroupIds = unfinishedGroups.map((group) => group.group_id)

  const advanceStage = async () => {
    if (!active || !stage || !nextStage) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const receipt = await sessionService.advanceLearningStage(active.sessionId, {
        expected_stage_revision: stage.stage_revision,
        target_stage: nextStage,
        ...(stage.stage === 'assistance' ? { assistance_disposition: 'not_needed' as const } : {}),
        unfinished_group_ids: unfinishedGroupIds,
        ...(unfinishedGroupIds.length ? { unfinished_group_disposition: 'save_draft' as const } : {}),
      })
      setStage({ ...stage, stage: receipt.stage, stage_revision: receipt.stage_revision })
      const latest = await sessionService.readSession(active.sessionId)
      setSession(latest)
      const updated = { ...active, revision: latest.revision, state: latest.state }
      saveActiveSession(updated)
      setActive(updated)
      setDraftAcknowledged(false)
      setAssistanceNotNeeded(false)
      setNotice(receipt.saved_drafts.length
        ? `BE1 đã lưu ${receipt.saved_drafts.length} bản nháp cho nhóm chưa hoàn tất trước khi chuyển chặng.`
        : `BE1 đã lưu xác nhận chuyển sang “${stageLabels[receipt.stage]}”.`)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'BE1 chưa thể chuyển chặng học.')
    } finally {
      setBusy(false)
    }
  }

  const endSession = async (completed: boolean) => {
    if (!active || !stage) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const receipt = await sessionService.completeSession(active.sessionId, {
        expected_stage_revision: stage.stage_revision,
        outcome: completed ? 'completed' : 'ended_early',
        ...(completed ? {} : { reason_category: earlyReason, teacher_note: teacherNote.trim() || undefined }),
      })
      setOutcome(receipt.outcome)
      const latest = await sessionService.readSession(active.sessionId)
      setSession(latest)
      const updated = { ...active, revision: latest.revision, state: latest.state, joinCode: undefined, roomCode: undefined }
      saveActiveSession(updated)
      setActive(updated)
      setNotice(completed ? 'BE1 đã lưu kết quả hoàn tất.' : `BE1 đã lưu kết thúc sớm (${earlyReason}).`)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'BE1 chưa thể lưu kết quả buổi học.')
    } finally {
      setBusy(false)
    }
  }

  const giveGroupTurn = async (childId: string) => {
    if (!active) return
    const group = active.groups[0]
    if (!group) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const receipt = await sessionService.startChildTurn(active.sessionId, group.groupId, childId)
      const updated = {
        ...active,
        turns: [...active.turns.filter((turn) => turn.groupId !== group.groupId), {
          childId,
          groupId: group.groupId,
          turnId: receipt.turn_id,
        }],
      }
      saveActiveSession(updated)
      setActive(updated)
      setNotice(`Lượt vẽ của ${active.admittedChildren.find((child) => child.childId === childId)?.displayName ?? 'trẻ'} đã được BE1 mở.`)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'BE1 chưa thể mở lượt vẽ.')
    } finally {
      setBusy(false)
    }
  }

  if (!active) return <main className="m-7 rounded-2xl border border-slate-200 bg-white p-7"><h1 className="text-2xl font-bold text-slate-900">Chưa có phiên BE1 đang chạy</h1><p className="mt-2 text-sm text-slate-600">Mở phiên từ phòng chờ đã kết nối.</p></main>

  const currentTurn = (groupId: string) => active.turns.find((turn) => turn.groupId === groupId)

  return (
    <main className="mx-auto max-w-6xl space-y-5 px-7 py-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-blue-700">Điều phối BE1 · {session?.state ?? active.state}</p>
          <h1 className="mt-1 text-3xl font-extrabold text-slate-900">{active.title}</h1>
          <p className="mt-2 text-sm text-slate-600">Session {active.sessionId} · {active.admittedChildren.length} trẻ đã được tiếp nhận · {active.groups.length} nhóm</p>
        </div>
        <div className="flex gap-2">
          {session?.state === 'active' && <button disabled={busy} onClick={() => void transition('pause')} className="rounded-xl border border-slate-300 px-4 py-3 font-semibold text-slate-800 disabled:opacity-50">Tạm dừng BE1</button>}
          {session?.state === 'paused' && <button disabled={busy} onClick={() => void transition('resume')} className="rounded-xl bg-blue-700 px-4 py-3 font-semibold text-white disabled:opacity-50">Tiếp tục BE1</button>}
        </div>
      </header>

      {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</div>}
      {notice && <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">{notice}</div>}

      {outcome && <div role="status" className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-900">Kết quả đã lưu trên BE1: {outcome === 'completed' ? 'Hoàn tất đủ quy trình' : 'Giáo viên kết thúc sớm'}.</div>}

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <h2 className="mb-4 text-lg font-bold text-slate-900">Nhóm và lượt vẽ được BE1 cấp</h2>
        <div className="space-y-4">
          {active.groups.map((group) => {
            const turn = currentTurn(group.groupId)
            const members = active.admittedChildren.filter((child) => group.childIds.includes(child.childId))
            return <article key={group.groupId} className="rounded-xl border border-slate-200 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div><h3 className="font-bold text-slate-900">{group.displayName}</h3><p className="text-sm text-slate-600">{members.length} trẻ · {active.drawMode === 'group' ? 'lượt vẽ tuần tự' : 'tranh cá nhân'}</p></div>
                <p className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-800">{turn ? `Đang vẽ: ${active.admittedChildren.find((child) => child.childId === turn.childId)?.displayName ?? 'trẻ'}` : 'Chưa có lượt hoạt động'}</p>
              </div>
              {active.drawMode === 'group' && members.length > 1 && <div className="mt-4 flex flex-wrap gap-2">
                {members.map((child) => <button key={child.childId} disabled={busy || turn?.childId === child.childId || session?.state !== 'active'} onClick={() => void giveGroupTurn(child.childId)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-40">Mở lượt cho {child.displayName}</button>)}
              </div>}
            </article>
          })}
          {active.groups.length === 0 && <p className="text-sm text-slate-600">Không tìm thấy nhóm được lưu trong phiên trình duyệt này.</p>}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <h2 className="mb-3 text-lg font-bold text-slate-900">Chặng học</h2>
        {stage ? <>
          <p className="text-xl font-extrabold text-slate-900">{stageLabels[stage.stage]}</p>
          <p className="mt-1 text-xs text-slate-500">BE1 stage revision {stage.stage_revision} · lifecycle {stage.lifecycle_state} · session revision {session?.revision ?? active.revision}</p>
          <ol className="mt-4 grid gap-2 sm:grid-cols-3 lg:grid-cols-5">
            {stageOrder.map((item, index) => <li key={item} className={`rounded-lg px-3 py-2 text-xs font-semibold ${index < currentStageIndex ? 'bg-emerald-50 text-emerald-800' : item === stage.stage ? 'bg-blue-100 text-blue-900' : 'bg-slate-50 text-slate-500'}`}>{index + 1}. {stageLabels[item]}</li>)}
          </ol>
          {unfinishedGroups.length > 0 && <label className="mt-4 flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-950">
            <input type="checkbox" checked={draftAcknowledged} onChange={(event) => setDraftAcknowledged(event.target.checked)} />
            <span>Trước khi chuyển chặng, yêu cầu BE1 lưu nháp cho {unfinishedGroups.length} nhóm chưa hoàn tất. Bản nháp giữ tham chiếu checkpoint/nét vẽ và không đánh dấu nhóm hoàn tất.</span>
          </label>}
          {stage.stage === 'assistance' && <label className="mt-3 flex items-center gap-2 rounded-lg bg-violet-50 p-3 text-sm text-violet-950">
            <input type="checkbox" checked={assistanceNotNeeded} onChange={(event) => setAssistanceNotNeeded(event.target.checked)} />
            <span>Không nhóm nào cần trợ giúp trong chặng này.</span>
          </label>}
          {nextStage && <div className="mt-4 flex flex-wrap items-center gap-3">
            <button disabled={busy || outcome !== null || (unfinishedGroups.length > 0 && !draftAcknowledged) || (stage.stage === 'assistance' && !assistanceNotNeeded)} onClick={() => void advanceStage()} className="rounded-lg bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{busy ? 'Đang lưu…' : `Lưu và chuyển: ${stageLabels[nextStage]}`}</button>
            {['knowledge', 'off_screen', 'reflection'].includes(stage.stage) && <span className="text-xs text-amber-900">Chặng tiếp theo đang khóa tới khi có hợp đồng BE2/media/hoạt động hoặc phản hồi trẻ được duyệt.</span>}
          </div>}
          {stage.stage === 'completion' && !outcome && <button disabled={busy} onClick={() => void endSession(true)} className="mt-4 rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">Lưu hoàn tất đủ quy trình</button>}
        </> : <p className="text-sm text-amber-900">Chưa đọc được trạng thái chặng có thẩm quyền từ BE1.</p>}
      </section>

      {(session?.state === 'active' || session?.state === 'paused') && !outcome && <section className="rounded-2xl border border-rose-200 bg-white p-5">
        <h2 className="text-lg font-bold text-slate-900">Kết thúc sớm</h2>
        <p className="mt-1 text-sm text-slate-600">BE1 lưu kết quả riêng với lifecycle. Chọn lý do bắt buộc; ghi chú là tùy chọn.</p>
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <label className="text-sm font-medium text-slate-700">Lý do
            <select value={earlyReason} onChange={(event) => setEarlyReason(event.target.value as typeof earlyReason)} className="mt-1 block rounded-lg border border-slate-300 bg-white px-3 py-2">
              <option value="time">Thiếu thời gian</option><option value="safety">An toàn</option><option value="technical">Sự cố kỹ thuật</option><option value="other">Khác</option>
            </select>
          </label>
          <label className="min-w-64 flex-1 text-sm font-medium text-slate-700">Ghi chú (tùy chọn)
            <input value={teacherNote} onChange={(event) => setTeacherNote(event.target.value.slice(0, 240))} className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2" maxLength={240} />
          </label>
          <button disabled={busy} onClick={() => void endSession(false)} className="rounded-lg border border-rose-300 bg-rose-50 px-4 py-2.5 text-sm font-semibold text-rose-800 disabled:opacity-50">Lưu kết thúc sớm</button>
        </div>
      </section>}
    </main>
  )
}
