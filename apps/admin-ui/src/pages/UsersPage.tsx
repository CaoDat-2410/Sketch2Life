import { useEffect, useState, type FormEvent } from 'react'
import { authService } from '../services/authService'
import { userService, type AccountRole, type AccountState, type ManagedAccount } from '../services/userService'

const ROLE_LABELS: Record<AccountRole, string> = {
  parent: 'Phụ huynh',
  teacher: 'Giáo viên',
  school_manager: 'Quản lý trường',
  platform_admin: 'Quản trị nền tảng',
}

const ROLE_OPTIONS: AccountRole[] = ['parent', 'teacher', 'school_manager', 'platform_admin']
const PAGE_SIZE = 50

export function UsersPage() {
  const [accounts, setAccounts] = useState<ManagedAccount[]>([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<AccountRole | ''>('')
  const [stateFilter, setStateFilter] = useState<AccountState | ''>('')
  const [offset, setOffset] = useState(0)
  const [roleEdits, setRoleEdits] = useState<Record<string, AccountRole | ''>>({})
  const [creating, setCreating] = useState(false)
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [newRole, setNewRole] = useState<AccountRole>('teacher')
  const [organizationId, setOrganizationId] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadAccounts = async (pageOffset = offset) => {
    setBusy(true)
    setError('')
    try {
      const page = await userService.listUsers({
        search: search.trim() || undefined,
        role: roleFilter || undefined,
        state: stateFilter || undefined,
        limit: PAGE_SIZE,
        offset: pageOffset,
      })
      setAccounts(page.items)
      setTotal(page.total)
      setRoleEdits(Object.fromEntries(page.items.map((account) => [account.account_id, account.role ?? ''])))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không tải được danh sách tài khoản.')
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => { void loadAccounts() }, [])

  const createAccount = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await userService.createAccount({
        email: email.trim(),
        display_name: displayName.trim(),
        role: newRole,
        ...(newRole === 'school_manager' ? { organization_id: organizationId.trim() } : {}),
      })
      setEmail('')
      setDisplayName('')
      setOrganizationId('')
      setCreating(false)
      setOffset(0)
      let resetEmailSent = true
      try {
        await authService.resetPassword(email.trim())
      } catch {
        resetEmailSent = false
      }
      setNotice(resetEmailSent
        ? 'Đã tạo tài khoản Firebase, cấp role và yêu cầu Firebase gửi email đặt mật khẩu.'
        : 'Đã tạo tài khoản Firebase và cấp role, nhưng chưa gửi được email đặt mật khẩu. Người dùng có thể chọn “Quên mật khẩu” ở màn đăng nhập.')
      await loadAccounts(0)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không tạo được tài khoản.')
    } finally {
      setBusy(false)
    }
  }

  const saveRole = async (account: ManagedAccount) => {
    const role = roleEdits[account.account_id]
    if (!role || role === account.role) return
    const org = role === 'school_manager'
      ? window.prompt('Nhập mã tổ chức cho Quản lý trường:')?.trim()
      : undefined
    if (role === 'school_manager' && !org) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await userService.updateAccount(account.account_id, {
        role,
        ...(org ? { organization_id: org } : {}),
      })
      setNotice('Đã cập nhật role. Các phân công BE1 không còn phù hợp đã bị thu hồi.')
      await loadAccounts()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không cập nhật được role.')
    } finally {
      setBusy(false)
    }
  }

  const toggleState = async (account: ManagedAccount) => {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await userService.updateAccount(account.account_id, {
        state: account.state === 'active' ? 'disabled' : 'active',
      })
      setNotice(account.state === 'active' ? 'Đã khóa tài khoản và thu hồi refresh token.' : 'Đã mở lại tài khoản.')
      await loadAccounts()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Không đổi được trạng thái tài khoản.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="mx-auto max-w-6xl space-y-5 p-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-blue-700">Quản trị nền tảng</p>
          <h1 className="mt-1 text-3xl font-extrabold text-slate-900">Tài khoản &amp; vai trò</h1>
          <p className="mt-2 text-sm text-slate-600">Role được lưu ở backend. Teacher vẫn cần School Manager phân công lớp để truy cập dữ liệu trường.</p>
        </div>
        <button onClick={() => setCreating((value) => !value)} className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700">{creating ? 'Đóng' : 'Tạo tài khoản'}</button>
      </header>

      {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</div>}
      {notice && <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div>}

      {creating && (
        <form onSubmit={(event) => void createAccount(event)} className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-5 md:grid-cols-2">
          <h2 className="md:col-span-2 text-lg font-bold text-slate-900">Tạo danh tính Firebase</h2>
          <label className="space-y-1 text-sm font-medium text-slate-700">Email<input required type="email" autoComplete="off" value={email} onChange={(event) => setEmail(event.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-2.5" /></label>
          <label className="space-y-1 text-sm font-medium text-slate-700">Tên hiển thị<input required maxLength={200} value={displayName} onChange={(event) => setDisplayName(event.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-2.5" /></label>
          <label className="space-y-1 text-sm font-medium text-slate-700">Vai trò<select value={newRole} onChange={(event) => setNewRole(event.target.value as AccountRole)} className="w-full rounded-xl border border-slate-200 px-3 py-2.5">{ROLE_OPTIONS.map((role) => <option key={role} value={role}>{ROLE_LABELS[role]}</option>)}</select></label>
          {newRole === 'school_manager' && <label className="space-y-1 text-sm font-medium text-slate-700">Mã tổ chức<input required value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-2.5" /></label>}
          <p className="md:col-span-2 text-xs text-slate-500">Tài khoản được tạo không kèm mật khẩu. Người dùng tự đặt mật khẩu qua email khôi phục Firebase. Tạo Teacher không tự cấp quyền vào lớp.</p>
          <div className="md:col-span-2"><button disabled={busy} className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60">{busy ? 'Đang tạo…' : 'Tạo tài khoản'}</button></div>
        </form>
      )}

      <div className="flex flex-wrap gap-3 rounded-2xl border border-slate-200 bg-white p-4">
        <input aria-label="Tìm tài khoản" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Email hoặc tên hiển thị" className="min-w-60 flex-1 rounded-xl border border-slate-200 px-3 py-2.5 text-sm" />
        <select aria-label="Lọc vai trò" value={roleFilter} onChange={(event) => setRoleFilter(event.target.value as AccountRole | '')} className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm"><option value="">Tất cả role</option>{ROLE_OPTIONS.map((role) => <option key={role} value={role}>{ROLE_LABELS[role]}</option>)}</select>
        <select aria-label="Lọc trạng thái" value={stateFilter} onChange={(event) => setStateFilter(event.target.value as AccountState | '')} className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm"><option value="">Tất cả trạng thái</option><option value="active">Đang hoạt động</option><option value="disabled">Đã khóa</option></select>
        <button onClick={() => { setOffset(0); void loadAccounts(0) }} disabled={busy} className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 disabled:opacity-60">Tìm</button>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-slate-50 text-slate-600"><tr><th className="px-4 py-3 font-semibold">Tài khoản</th><th className="px-4 py-3 font-semibold">Vai trò</th><th className="px-4 py-3 font-semibold">Trạng thái</th><th className="px-4 py-3 font-semibold">Revision</th><th className="px-4 py-3 font-semibold">Thao tác</th></tr></thead>
          <tbody className="divide-y divide-slate-100">
            {accounts.map((account) => (
              <tr key={account.account_id}>
                <td className="px-4 py-3"><div className="font-semibold text-slate-900">{account.display_name || 'Chưa có tên'}</div><div className="text-xs text-slate-500">{account.email || 'Chưa có email'}</div></td>
                <td className="px-4 py-3"><select aria-label={`Vai trò ${account.email ?? account.account_id}`} value={roleEdits[account.account_id] ?? account.role ?? ''} onChange={(event) => setRoleEdits((current) => ({ ...current, [account.account_id]: event.target.value as AccountRole | '' }))} className="rounded-lg border border-slate-200 px-2 py-1.5"><option value="">Chưa gán vai trò</option>{ROLE_OPTIONS.map((role) => <option key={role} value={role}>{ROLE_LABELS[role]}</option>)}</select></td>
                <td className="px-4 py-3">{account.state === 'active' ? 'Đang hoạt động' : 'Đã khóa'}</td>
                <td className="px-4 py-3 text-slate-500">{account.revision}</td>
                <td className="px-4 py-3"><div className="flex gap-2"><button disabled={busy || !roleEdits[account.account_id] || roleEdits[account.account_id] === account.role} onClick={() => void saveRole(account)} className="rounded-lg border border-blue-200 px-3 py-1.5 text-xs font-semibold text-blue-700 disabled:opacity-40">Lưu role</button><button disabled={busy} onClick={() => void toggleState(account)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 disabled:opacity-40">{account.state === 'active' ? 'Khóa' : 'Mở lại'}</button></div></td>
              </tr>
            ))}
            {!busy && accounts.length === 0 && <tr><td colSpan={5} className="px-4 py-10 text-center text-slate-500">Không có tài khoản phù hợp.</td></tr>}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-500">Hiển thị {accounts.length} trên {total} tài khoản. Role change và khóa tài khoản được ghi audit; account ID là mã nội bộ opaque.</p>
        <div className="flex gap-2">
          <button disabled={busy || offset === 0} onClick={() => { const next = Math.max(0, offset - PAGE_SIZE); setOffset(next); void loadAccounts(next) }} className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm disabled:opacity-40">Trước</button>
          <button disabled={busy || offset + accounts.length >= total} onClick={() => { const next = offset + PAGE_SIZE; setOffset(next); void loadAccounts(next) }} className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm disabled:opacity-40">Tiếp</button>
        </div>
      </div>
    </section>
  )
}
