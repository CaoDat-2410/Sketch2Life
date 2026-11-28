import { AdminSelect } from '../components/AdminSelect'
import { Mail } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { BackendApiError, hasFirebaseAuthBridge } from '../../../shared/api/backendApi'
import { usePortalSession } from '../../../shared/auth/PortalSessionContext'
import { MgIcon } from '../components/MgIcon'
import { Heading } from '../components/AdminUI'
import { useAdminQuery } from '../components/adminHooks'
import { AdminSearchInput } from '../components/AdminSearchInput'
import { AccessibleDialog } from '../../../shared/components/ui'

import { readAllPages, commandClient, type Organization } from '../services/adminService'
import { keyForSignature, userService, type AccountRole, type AccountState, type ManagedAccount } from '../services/userService'

const ROLE_LABELS: Record<AccountRole, string> = { parent: 'Phụ huynh', teacher: 'Giáo viên', school_manager: 'Quản lý trường', platform_admin: 'Quản trị nền tảng' }
const ROLE_OPTIONS: AccountRole[] = ['parent', 'teacher', 'school_manager', 'platform_admin']
// SRS UC-13: the School Manager invites Teachers. An Admin-created Teacher would have no organization.
const CREATE_ROLE_OPTIONS: AccountRole[] = ROLE_OPTIONS.filter((role) => role !== 'teacher')
const PAGE_SIZE = 25
type Filters = { search: string; role: AccountRole | ''; state: AccountState | '' }
type LoadState = 'loading' | 'ready' | 'error'
type LoadFailure = { title: string; message: string; auth: boolean; denied: boolean }

function toLoadFailure(cause: unknown): LoadFailure {
  const apiError = cause instanceof BackendApiError ? cause : null
  const auth = apiError?.status === 401 || apiError?.code === 'AUTHENTICATION_REQUIRED'
  const denied = apiError?.status === 403
  return {
    title: auth ? 'Phiên xác thực cần đăng nhập lại' : denied ? 'Tài khoản chưa có quyền quản lý' : 'Không tải được danh sách tài khoản',
    message: cause instanceof Error ? cause.message : 'Backend chưa trả về thông tin lỗi chi tiết.',
    auth, denied,
  }
}

const messageFrom = (cause: unknown, fallback: string) => cause instanceof Error ? cause.message : fallback

function accountMutationErrorMessage(cause: unknown, fallback: string) {
  if (cause instanceof BackendApiError && cause.code === 'ORGANIZATION_UNAVAILABLE') {
    return 'Trường được chọn không tồn tại hoặc không còn hoạt động. Hãy tải lại danh sách và chọn một trường đang hoạt động.'
  }
  return messageFrom(cause, fallback)
}

function accountDisplayName(account: ManagedAccount): string | null {
  const name = account.display_name?.trim()
  if (!name || !account.role || !name.startsWith('[TEST] ')) return name || null
  const roleSuffix = ` · ${ROLE_LABELS[account.role]}`
  return name.endsWith(roleSuffix) ? name.slice(0, -roleSuffix.length) : name
}

export function UsersPage() {
  const navigate = useNavigate()
  const { logout } = usePortalSession()
  const [accounts, setAccounts] = useState<ManagedAccount[]>([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<AccountRole | ''>('')
  const [stateFilter, setStateFilter] = useState<AccountState | ''>('')
  const [hasAppliedFilters, setHasAppliedFilters] = useState(false)
  // FEAT-066 C5: cursor paging; pageStarts holds the start cursor of every page shown so far.
  const [pageStarts, setPageStarts] = useState<(string | null)[]>([null])
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const mutationKeys = useRef(new Map<string, string>())
  const loadSequence = useRef(0)
  const [roleEdits, setRoleEdits] = useState<Record<string, AccountRole | ''>>({})
  const [organizationEdits, setOrganizationEdits] = useState<Record<string, string>>({})
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [loadFailure, setLoadFailure] = useState<LoadFailure | null>(null)
  const [creating, setCreating] = useState(false)
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [newRole, setNewRole] = useState<AccountRole>('school_manager')
  const [organizationId, setOrganizationId] = useState('')
  const [mutating, setMutating] = useState(false)
  const [actionError, setActionError] = useState('')
  const [notice, setNotice] = useState('')
  const [stateTarget, setStateTarget] = useState<ManagedAccount | null>(null)
  const [emailTarget, setEmailTarget] = useState<ManagedAccount | null>(null)
  const [sendCommand] = useState(commandClient)
  const emailSending = useRef(false)
  const needsSchools = (creating && newRole === 'school_manager') || accounts.some(a => roleEdits[a.account_id] === 'school_manager' && a.role !== 'school_manager')
  const schools = useAdminQuery(() => needsSchools ? readAllPages<Organization>('/organizations') : Promise.resolve({items: [] as Organization[], total: 0}), String(needsSchools))
  const activeSchools = (schools.data?.items ?? []).filter((school) => school.state?.trim().toLowerCase() === 'active')
  const noActiveSchools = needsSchools && !schools.loading && !schools.error && Boolean(schools.data) && activeSchools.length === 0


  const loadAccounts = async (starts: (string | null)[] = pageStarts, filters: Filters = { search, role: roleFilter, state: stateFilter }) => {
    const sequence = ++loadSequence.current
    setLoadState('loading')
    setLoadFailure(null)
    setPageStarts(starts)
    setNextCursor(null)
    if (!hasFirebaseAuthBridge()) {
      setAccounts([]); setTotal(0)
      setLoadFailure({ title: 'Chưa có phiên Firebase Authentication', message: 'Cổng Platform Admin đang mở nhưng chưa có Firebase ID token để backend xác minh. Đăng nhập lại bằng tài khoản Platform Admin.', auth: true, denied: false })
      setLoadState('error')
      return
    }
    try {
      const start = starts[starts.length - 1] ?? undefined
      const page = await userService.listUsers({ search: filters.search.trim() || undefined, role: filters.role || undefined, state: filters.state || undefined, limit: PAGE_SIZE, cursor: start })
      if (sequence !== loadSequence.current) return
      setAccounts(page.items)
      setTotal(page.total)
      setNextCursor(page.next_cursor ?? null)
      setRoleEdits(Object.fromEntries(page.items.map((account) => [account.account_id, account.role ?? ''])))
      setOrganizationEdits({})
      setLoadState('ready')
    } catch (cause) {
      if (sequence !== loadSequence.current) return
      setAccounts([]); setTotal(0)
      setLoadFailure(toLoadFailure(cause))
      setLoadState('error')
    }
  }

  useEffect(() => {
    void Promise.resolve().then(() => loadAccounts([null], { search: '', role: '', state: '' }))
  }, [])

  const submitFilters = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setHasAppliedFilters(Boolean(search.trim() || roleFilter || stateFilter))
    setActionError(''); setNotice('')
    void loadAccounts([null], { search, role: roleFilter, state: stateFilter })
  }

  const clearFilters = () => {
    setSearch(''); setRoleFilter(''); setStateFilter(''); setHasAppliedFilters(false); setActionError('')
    void loadAccounts([null], { search: '', role: '', state: '' })
  }

  const createAccount = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (mutating || loadState !== 'ready' || !hasFirebaseAuthBridge()) return
    const submittedEmail = email.trim()
    setMutating(true); setActionError(''); setNotice('')
    const payload = { email: submittedEmail, display_name: displayName.trim(), role: newRole, ...(newRole === 'school_manager' ? { organization_id: organizationId.trim() } : {}) }
    const signature = JSON.stringify(['create-account', payload])
    try {
      await userService.createAccount(payload, keyForSignature(mutationKeys.current, signature))
      mutationKeys.current.delete(signature)
      setEmail(''); setDisplayName(''); setOrganizationId(''); setCreating(false)
      setNotice('Đã tạo tài khoản. Email thiết lập mật khẩu đã được đưa vào hàng đợi gửi.')
      setSearch(''); setRoleFilter(''); setStateFilter(''); setHasAppliedFilters(false)
      await loadAccounts([null], { search: '', role: '', state: '' })
    } catch (cause) { setActionError(accountMutationErrorMessage(cause, 'Không tạo được tài khoản.')) }
    finally { setMutating(false) }
  }

  const saveRole = async (account: ManagedAccount) => {
    const role = roleEdits[account.account_id]
    if (mutating || !role || role === account.role || loadState !== 'ready' || !hasFirebaseAuthBridge()) return
    const org = role === 'school_manager' ? organizationEdits[account.account_id]?.trim() : undefined
    if (role === 'school_manager' && !org) { setActionError('Nhập mã tổ chức trước khi gán vai trò Quản lý trường.'); return }
    setMutating(true); setActionError(''); setNotice('')
    const payload = { role, ...(org ? { organization_id: org } : {}) }
    const signature = JSON.stringify(['update-account', account.account_id, account.revision, payload])
    try {
      await userService.updateAccount(account.account_id, payload, keyForSignature(mutationKeys.current, signature), account.revision)
      mutationKeys.current.delete(signature)
      setNotice('Đã cập nhật vai trò. Quyền truy cập lớp vẫn cần phân công riêng bởi Quản lý trường.')
      await loadAccounts()
    } catch (cause) { setActionError(accountMutationErrorMessage(cause, 'Không cập nhật được vai trò.')) }
    finally { setMutating(false) }
  }

  const toggleState = async (account: ManagedAccount) => {
    if (mutating || loadState !== 'ready' || !hasFirebaseAuthBridge()) return
    setMutating(true); setActionError(''); setNotice('')
    const payload = { state: account.state === 'disabled' ? 'active' as const : 'disabled' as const }
    const signature = JSON.stringify(['update-account', account.account_id, account.revision, payload])
    try {
      await userService.updateAccount(account.account_id, payload, keyForSignature(mutationKeys.current, signature), account.revision)
      mutationKeys.current.delete(signature)
      setStateTarget(null)
      setNotice(account.state === 'disabled' ? 'Đã mở lại tài khoản. Tài khoản mới vẫn cần xác minh email.' : 'Đã khóa tài khoản và thu hồi phiên đăng nhập.')
      await loadAccounts()
    } catch (cause) { setActionError(messageFrom(cause, 'Không đổi được trạng thái tài khoản.')) }
    finally { setMutating(false) }
  }

  const loginAgain = () => { logout(); navigate('/login?role=admin', { replace: true }) }
  const resendSetupEmail = async () => {
    if (!emailTarget || emailSending.current || mutating) return
    emailSending.current = true
    setMutating(true); setActionError(''); setNotice('')
    try {
      await sendCommand('/accounts/' + encodeURIComponent(emailTarget.account_id) + '/setup-email')
      setEmailTarget(null)
      setNotice('Đã đưa email thiết lập mật khẩu vào hàng đợi. Theo dõi kết quả trong Email hệ thống.')
    } catch (cause) { setActionError(messageFrom(cause, 'Không gửi được yêu cầu email.')) }
    finally { emailSending.current = false; setMutating(false) }
  }
  const filtersDisabled = loadState !== 'ready' || mutating
  const canManage = loadState === 'ready' && !mutating
  const pages = total ? Math.ceil(total / PAGE_SIZE) : 0
  const currentPage = pages ? pageStarts.length : 0
  const pageStartIndex = (pageStarts.length - 1) * PAGE_SIZE
  const rangeStart = total ? pageStartIndex + 1 : 0
  const rangeEnd = Math.min(pageStartIndex + accounts.length, total)

  return (
    <section className='platform-accounts' aria-label='Tài khoản và vai trò'>
      <Heading title='Tài khoản và vai trò'>
        <button type='button' className='accounts-button accounts-button-primary' disabled={!canManage} onClick={() => { setCreating((value) => !value); setActionError('') }}><MgIcon name={creating ? 'close' : 'plus'} size={18} />{creating ? 'Đóng biểu mẫu' : 'Tạo tài khoản'}</button>
      </Heading>

      {notice && <div className='accounts-feedback is-success' role='status'><span aria-hidden='true'><MgIcon name='check' size={18} /></span><p>{notice}</p></div>}
      {actionError && <div className='accounts-feedback is-error' role='alert'><span aria-hidden='true'><MgIcon name='alert' size={18} /></span><p>{actionError}</p></div>}

      {loadFailure && <section className={`accounts-load-error ${loadFailure.auth ? 'is-warning' : loadFailure.denied ? 'is-denied' : ''}`} role='alert' aria-labelledby='accounts-error-title'>
        <span className='accounts-error-icon' aria-hidden='true'><MgIcon name={loadFailure.auth ? 'lock' : 'alert'} size={22} /></span>
        <div className='accounts-error-copy'><h2 id='accounts-error-title'>{loadFailure.title}</h2><p>{loadFailure.message}</p></div>
        <div className='accounts-error-actions'><button type='button' className='accounts-button accounts-button-secondary' onClick={() => void loadAccounts()} disabled={loadState === 'loading'}><MgIcon name='refresh' size={17} />Thử tải lại</button>{loadFailure.auth && <button type='button' className='accounts-button accounts-button-primary' onClick={loginAgain}>Đăng nhập lại</button>}</div>
      </section>}

      {noActiveSchools && <p className='accounts-form-hint' role='status'>Hiện không có trường nào ở trạng thái đang hoạt động. Chỉ trường đang hoạt động mới có thể được chọn để gán vai trò Quản lý trường.</p>}

      {creating && loadState === 'ready' && <form className='accounts-panel accounts-create-form' onSubmit={(event) => void createAccount(event)} aria-busy={mutating}>
        <div className='accounts-panel-heading'><div><p className='accounts-eyebrow'>Danh tính mới</p><h2>Tạo tài khoản</h2></div><span className='accounts-panel-mark' aria-hidden='true'><MgIcon name='userplus' size={21} /></span></div>
        <div className='accounts-form-grid'>
          <label className='accounts-field'><span>Email tài khoản</span><input required type='email' autoComplete='email' value={email} onChange={(event) => setEmail(event.target.value)} disabled={mutating} /></label>
          <label className='accounts-field'><span>Tên hiển thị</span><input required maxLength={200} autoComplete='name' value={displayName} onChange={(event) => setDisplayName(event.target.value)} disabled={mutating} /></label>
          <label className='accounts-field'><span>Vai trò sản phẩm</span><AdminSelect aria-label='Vai trò sản phẩm' value={newRole} onChange={(event) => setNewRole(event.target.value as AccountRole)} disabled={mutating}>{CREATE_ROLE_OPTIONS.map((role) => <option key={role} value={role}>{ROLE_LABELS[role]}</option>)}</AdminSelect></label>
          {newRole === 'school_manager' && <label className='accounts-field'><span>Trường học</span><AdminSelect required aria-label='Trường học cho tài khoản mới' value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} disabled={mutating || schools.loading || activeSchools.length === 0}><option value=''>{activeSchools.length ? 'Chọn trường học' : 'Không có trường đang hoạt động'}</option>{activeSchools.map(o => <option key={o.organization_id} value={o.organization_id}>{o.display_name}</option>)}</AdminSelect></label>}
        </div>
        <p className='accounts-form-hint'>Người nhận được gửi email hướng dẫn đặt mật khẩu. Tài khoản giáo viên do Quản lý trường mời.</p>
        <div className='accounts-form-actions'><button type='button' className='accounts-button accounts-button-secondary' onClick={() => setCreating(false)} disabled={mutating}>Hủy</button><button type='submit' className='accounts-button accounts-button-primary' disabled={mutating || (newRole === 'school_manager' && (schools.loading || activeSchools.length === 0))}><MgIcon name={mutating ? 'refresh' : 'plus'} size={18} />{mutating ? 'Đang tạo tài khoản…' : 'Tạo tài khoản'}</button></div>
      </form>}

      <div className='koi-accounts-band'>
      {loadState !== 'error' && <div className='accounts-list-heading'><div className='accounts-directory-title'><span className='accounts-directory-icon' aria-hidden='true'><MgIcon name='users' size={22} /></span><h2 id='accounts-list-title'>Tài khoản người dùng</h2></div><div className='accounts-row-actions'>{loadState === 'ready' && <span className='accounts-result-pill' aria-live='polite'>{total.toLocaleString('vi-VN')} tài khoản</span>}<button type='button' className='accounts-button accounts-button-small accounts-button-secondary' disabled={loadState === 'loading' || mutating} onClick={() => { setActionError(''); setNotice(''); void loadAccounts() }}><MgIcon name='refresh' size={16} />Tải lại</button></div></div>}
      <form className='accounts-filters accounts-panel' onSubmit={submitFilters} aria-label='Lọc danh sách tài khoản'>
        <AdminSearchInput className='accounts-search-slot' label='Tìm tài khoản theo email hoặc tên hiển thị' value={search} onValueChange={setSearch} placeholder='Email hoặc tên hiển thị' disabled={filtersDisabled} />
        <label className='accounts-select-field'><span className='accounts-visually-hidden'>Lọc theo vai trò</span><AdminSelect aria-label='Lọc theo vai trò' value={roleFilter} onChange={(event) => setRoleFilter(event.target.value as AccountRole | '')} disabled={filtersDisabled}><option value=''>Tất cả vai trò</option>{ROLE_OPTIONS.map((role) => <option key={role} value={role}>{ROLE_LABELS[role]}</option>)}</AdminSelect></label>
        <label className='accounts-select-field'><span className='accounts-visually-hidden'>Lọc theo trạng thái tài khoản</span><AdminSelect aria-label='Lọc theo trạng thái tài khoản' value={stateFilter} onChange={(event) => setStateFilter(event.target.value as AccountState | '')} disabled={filtersDisabled}><option value=''>Tất cả trạng thái</option><option value='active'>Đang hoạt động</option><option value='disabled'>Đã khóa</option><option value='pending_verification'>Chờ xác minh email</option></AdminSelect></label>
        <button type='submit' className='accounts-button accounts-button-secondary' disabled={filtersDisabled}>Tìm tài khoản</button>
      </form>
      </div>

      {loadState !== 'error' && <section className='accounts-panel accounts-list-panel' aria-labelledby='accounts-list-title' aria-busy={loadState === 'loading'}>
        {loadState === 'loading' && <div className='accounts-list-state' role='status' aria-live='polite'><span className='accounts-spinner' aria-hidden='true' /><p>Đang tải danh sách tài khoản…</p></div>}
        {loadState === 'ready' && accounts.length === 0 && <div className='accounts-list-state is-empty-state'><span className='accounts-empty-icon' aria-hidden='true'><MgIcon name={hasAppliedFilters ? 'search' : 'users'} size={25} /></span><h3>{hasAppliedFilters ? 'Không tìm thấy tài khoản phù hợp' : 'Chưa có tài khoản'}</h3><p>{hasAppliedFilters ? 'Thử từ khóa hoặc bộ lọc khác.' : 'Tạo tài khoản đầu tiên để bắt đầu.'}</p>{hasAppliedFilters ? <button type='button' className='accounts-button accounts-button-secondary' onClick={clearFilters}>Xóa bộ lọc</button> : <button type='button' className='accounts-button accounts-button-secondary' onClick={() => setCreating(true)} disabled={!canManage}><MgIcon name='plus' size={17} />Tạo tài khoản đầu tiên</button>}</div>}

        {loadState === 'ready' && accounts.length > 0 && <div className='accounts-table-wrap'><table className='accounts-table'><thead><tr><th scope='col'>Tài khoản</th><th scope='col'>Vai trò</th><th scope='col'>Trạng thái</th><th scope='col'>Thao tác</th></tr></thead><tbody>
          {accounts.map((account) => {
            const role = roleEdits[account.account_id] ?? account.role ?? ''
            const changed = Boolean(role && role !== account.role)
            const needsOrganization = role === 'school_manager' && changed
            const orgValue = organizationEdits[account.account_id] ?? ''
            const label = account.email ?? account.account_id
            const displayName = accountDisplayName(account)
            return <tr key={account.account_id} data-account-role={account.role ?? 'unassigned'} data-role-edited={changed || undefined}>
              <td data-label='Tài khoản'><div className='accounts-person'><span className='accounts-avatar' aria-hidden='true'>{(displayName || account.email || '?').replace(/^\[TEST\]\s*/, '').trim().slice(0, 1).toLocaleUpperCase('vi-VN')}</span><span className='accounts-person-copy'><strong>{displayName || 'Chưa có tên'}</strong><span>{account.email || 'Chưa có email'}</span></span></div></td>
              <td data-label='Vai trò'><div className='accounts-role-editor'><label className='accounts-visually-hidden' htmlFor={`account-role-${account.account_id}`}>Vai trò của {label}</label><AdminSelect id={`account-role-${account.account_id}`} value={role} onChange={(event) => setRoleEdits((current) => ({ ...current, [account.account_id]: event.target.value as AccountRole | '' }))} disabled={!canManage}><option value=''>Chưa gán vai trò</option>{ROLE_OPTIONS.map((item) => <option key={item} value={item}>{ROLE_LABELS[item]}</option>)}</AdminSelect>{needsOrganization && <label className='accounts-inline-organization'><span>Trường học</span><AdminSelect required aria-label={`Trường học cho ${label}`} value={orgValue} onChange={(event) => setOrganizationEdits((current) => ({ ...current, [account.account_id]: event.target.value }))} disabled={!canManage || schools.loading || activeSchools.length === 0}><option value=''>{activeSchools.length ? 'Chọn trường học' : 'Không có trường đang hoạt động'}</option>{activeSchools.map(o => <option key={o.organization_id} value={o.organization_id}>{o.display_name}</option>)}</AdminSelect></label>}</div></td>
              <td data-label='Trạng thái'><span className={`accounts-status ${account.state === 'active' ? 'is-active' : account.state === 'pending_verification' ? 'is-pending' : 'is-disabled'}`}><span aria-hidden='true' />{account.state === 'active' ? 'Đang hoạt động' : account.state === 'pending_verification' ? 'Chờ xác minh email' : 'Đã khóa'}</span></td>
<td data-label='Thao tác'><div className='accounts-row-actions'>{account.state !== 'disabled' && account.email && <button type='button' className='accounts-button accounts-button-small accounts-button-secondary' disabled={!canManage} onClick={() => { setActionError(''); setEmailTarget(account) }}>Gửi email thiết lập</button>}{changed && <button type='button' className='accounts-button accounts-button-small accounts-button-primary' disabled={!canManage || !changed || (needsOrganization && !orgValue.trim())} onClick={() => void saveRole(account)}>Lưu vai trò</button>}<button type='button' className={`accounts-button accounts-button-small ${account.state === 'disabled' ? 'accounts-button-outline' : 'accounts-button-danger'}`} disabled={!canManage} onClick={() => { setActionError(''); setStateTarget(account) }}>{account.state === 'disabled' ? 'Mở lại' : 'Khóa tài khoản'}</button></div></td>
            </tr>
          })}
        </tbody></table></div>}

        {loadState === 'ready' && accounts.length > 0 && <footer className='accounts-pagination'><p>Đang hiển thị {rangeStart.toLocaleString('vi-VN')}–{rangeEnd.toLocaleString('vi-VN')} trên {total.toLocaleString('vi-VN')} tài khoản.</p><div className='accounts-pagination-controls'><span>Trang {currentPage} / {pages}</span><button type='button' className='accounts-button accounts-button-secondary' disabled={mutating || pageStarts.length <= 1} onClick={() => void loadAccounts(pageStarts.slice(0, -1))}><MgIcon name='arrow-left' size={17} />Trước</button><button type='button' className='accounts-button accounts-button-secondary' disabled={mutating || !nextCursor} onClick={() => { if (nextCursor) void loadAccounts([...pageStarts, nextCursor]) }}>Tiếp<MgIcon name='arrow-right' size={17} /></button></div></footer>}
      </section>}

      {needsSchools && schools.error && <p role='alert' className='pa-alert'>{schools.error} <button type='button' onClick={schools.reload}>Tải lại danh sách trường</button></p>}
      <AccessibleDialog className="platform-accounts accounts-email-dialog" open={Boolean(stateTarget)} onOpenChange={(open) => { if (!open && !mutating) setStateTarget(null) }} title="Đổi trạng thái tài khoản" description={stateTarget?.email || stateTarget?.account_id || ''} showClose={!mutating}>
        <h2>{stateTarget?.state === 'disabled' ? 'Mở lại tài khoản?' : 'Khóa tài khoản?'}</h2>
        <strong>{stateTarget?.email || stateTarget?.account_id}</strong>
        {stateTarget && stateTarget.state !== 'disabled' && <p>Người dùng sẽ bị đăng xuất.</p>}
        {actionError && <p role="alert">{actionError}</p>}
        <div className="accounts-row-actions">
          <button className="accounts-button" disabled={mutating} onClick={() => setStateTarget(null)}>Hủy</button>
          <button className="accounts-button accounts-button-primary" disabled={!stateTarget || mutating} onClick={() => stateTarget && void toggleState(stateTarget)}>Xác nhận</button>
        </div>
      </AccessibleDialog>
      <AccessibleDialog className='platform-accounts accounts-email-dialog' open={Boolean(emailTarget)} onOpenChange={(open) => { if (!open && !mutating) setEmailTarget(null) }} title='Gửi email thiết lập mật khẩu' description='Người nhận sẽ nhận liên kết để tự đặt mật khẩu. Không có mật khẩu nào được hiển thị cho quản trị viên.' showClose={!mutating}>
        <span className='accounts-email-icon' aria-hidden='true'><Mail size={24} /></span>
        <h2>Gửi email thiết lập mật khẩu</h2>
        <div className='accounts-email-recipient'><span>Người nhận</span><strong>{emailTarget ? accountDisplayName(emailTarget) || 'Tài khoản người dùng' : 'Tài khoản người dùng'}</strong><span>{emailTarget?.email}</span></div>
        <p className='accounts-email-hint'>Dùng liên kết trong email mới nhất. Gửi lại email không đổi mật khẩu hiện tại.</p>
        {actionError && <p role='alert'>{actionError}</p>}
        <div className='accounts-row-actions'>
          <button type='button' className='accounts-button accounts-button-secondary' disabled={mutating} onClick={() => setEmailTarget(null)}>Hủy</button>
          <button type='button' className='accounts-button accounts-button-primary' disabled={mutating} onClick={() => void resendSetupEmail()}>{mutating ? 'Đang gửi yêu cầu…' : 'Xác nhận gửi'}</button>
        </div>
      </AccessibleDialog>
    </section>
  )
}
