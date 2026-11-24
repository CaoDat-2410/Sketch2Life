import { useEffect, useState, type FormEvent } from 'react'
import {
  parentConsentPolicyService,
  type ParentConsentPolicy,
  type ParentConsentPolicyState,
} from '../services/parentConsentPolicyService'

const STATE_LABELS: Record<ParentConsentPolicyState, string> = {
  DRAFT: 'Bản nháp',
  ACTIVE: 'Đang áp dụng',
  RETIRED: 'Đã thay thế',
}

const STATE_STYLES: Record<ParentConsentPolicyState, string> = {
  DRAFT: 'bg-amber-50 text-amber-800 ring-amber-200',
  ACTIVE: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
  RETIRED: 'bg-slate-100 text-slate-600 ring-slate-200',
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('vi-VN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function ParentConsentPoliciesPage() {
  const [policies, setPolicies] = useState<ParentConsentPolicy[]>([])
  const [policyVersion, setPolicyVersion] = useState('')
  const [consentText, setConsentText] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadPolicies = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await parentConsentPolicyService.list()
      setPolicies(response.policies)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không tải được chính sách consent.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void loadPolicies() }, [])

  const createDraft = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await parentConsentPolicyService.createDraft({
        policy_version: policyVersion.trim(),
        consent_text: consentText.trim(),
      })
      setPolicyVersion('')
      setConsentText('')
      setNotice('Đã lưu bản nháp. Phụ huynh chưa thấy nội dung cho đến khi bản này được kích hoạt.')
      await loadPolicies()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không tạo được bản nháp.')
    } finally {
      setBusy(false)
    }
  }

  const activate = async (policy: ParentConsentPolicy) => {
    const accepted = window.confirm(
      `Kích hoạt phiên bản ${policy.policy_version}? Phiên bản đang áp dụng sẽ được lưu thành bản cũ.`,
    )
    if (!accepted) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await parentConsentPolicyService.activate(policy.policy_id)
      setNotice(`Đã kích hoạt phiên bản ${policy.policy_version}.`)
      await loadPolicies()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không kích hoạt được phiên bản.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="mx-auto max-w-6xl space-y-6 p-7">
      <header>
        <p className="text-sm font-semibold text-blue-700">Quản trị nền tảng</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">Consent dữ liệu trẻ</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Tạo phiên bản thông báo, rà soát nội dung rồi kích hoạt. Nội dung đã tạo không thể sửa;
          khi cần thay đổi, hãy tạo phiên bản mới.
        </p>
      </header>

      {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
      {notice && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.9fr)]">
        <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-bold text-slate-900">Các phiên bản</h2>
            <button
              type="button"
              onClick={() => void loadPolicies()}
              disabled={loading || busy}
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
            >
              Tải lại
            </button>
          </div>
          {loading ? <p className="text-sm text-slate-500">Đang tải…</p> : policies.length === 0 ? (
            <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">Chưa có phiên bản. Phụ huynh chưa thể cấp consent cho đến khi quản trị viên kích hoạt một chính sách.</p>
          ) : (
            <div className="space-y-3">
              {policies.map((policy) => (
                <article key={policy.policy_id} className="rounded-xl border border-slate-200 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-slate-900">{policy.policy_version}</h3>
                      <p className="mt-1 text-xs text-slate-500">Tạo lúc {formatDate(policy.created_at)}</p>
                    </div>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${STATE_STYLES[policy.state]}`}>
                      {STATE_LABELS[policy.state]}
                    </span>
                  </div>
                  <p className="mt-3 whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-sm leading-6 text-slate-700">{policy.consent_text}</p>
                  <p className="mt-2 break-all font-mono text-[11px] text-slate-400">SHA-256: {policy.consent_text_sha256}</p>
                  {policy.state === 'DRAFT' && (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => void activate(policy)}
                      className="mt-3 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                    >
                      Kích hoạt phiên bản
                    </button>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>

        <form onSubmit={(event) => void createDraft(event)} className="h-fit space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Tạo bản nháp</h2>
            <p className="mt-1 text-sm text-slate-600">Nhập nội dung đã được duyệt và một mã phiên bản mới.</p>
          </div>
          <label className="block space-y-1.5 text-sm font-semibold text-slate-700">
            Mã phiên bản
            <input
              required
              maxLength={80}
              pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,79}"
              value={policyVersion}
              onChange={(event) => setPolicyVersion(event.target.value)}
              placeholder="Ví dụ: parent-consent-v1"
              className="w-full rounded-xl border border-slate-300 px-3 py-2.5 font-normal outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </label>
          <label className="block space-y-1.5 text-sm font-semibold text-slate-700">
            Nội dung hiển thị cho phụ huynh
            <textarea
              required
              maxLength={4000}
              rows={10}
              value={consentText}
              onChange={(event) => setConsentText(event.target.value)}
              placeholder="Dán nguyên văn thông báo consent đã được duyệt."
              className="w-full resize-y rounded-xl border border-slate-300 px-3 py-2.5 font-normal leading-6 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
            <span className="block text-right text-xs font-normal text-slate-500">{consentText.length}/4000</span>
          </label>
          <button
            type="submit"
            disabled={busy || !policyVersion.trim() || !consentText.trim()}
            className="w-full rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
          >
            {busy ? 'Đang lưu…' : 'Lưu bản nháp'}
          </button>
        </form>
      </div>
    </section>
  )
}
