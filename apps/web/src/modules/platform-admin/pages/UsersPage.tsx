import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import '../../../shared/styles/tailwind-utilities.css'
import { BackendApiError, hasFirebaseAuthBridge } from '../../../shared/api/backendApi'
import { usePortalSession } from '../../../shared/auth/PortalSessionContext'
import { MgIcon } from '../components/MgIcon'
import '../styles/accounts-page.css'
import { authService } from '../../school-manager/be1/services/authService'
import { userService, type AccountRole, type AccountState, type ManagedAccount } from '../services/userService'

const ROLE_LABELS: Record<AccountRole, string> = { parent: 'Phụ huynh', teacher: 'Giáo viên', school_manager: 'Quản lý trường', platform_admin: 'Quản trị nền tảng' }
const ROLE_OPTIONS: AccountRole[] = ['parent', 'teacher', 'school_manager', 'platform_admin']
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

export function UsersPage() {
  const navigate = useNavigate()
  const { logout } = usePortalSession()
  const [accounts, setAccounts] = useState<ManagedAccount[]>([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<AccountRole | ''>('')
  const [stateFilter, setStateFilter] = useState<AccountState | ''>('')
  const [hasAppliedFilters, setHasAppliedFilters] = useState(false)
  const [offset, setOffset] = useState(0)
  const [roleEdits, setRoleEdits] = useState<Record<string, AccountRole | ''>>({})
  const [organizationEdits, setOrganizationEdits] = useState<Record<string, string>>({})
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [loadFailure, setLoadFailure] = useState<LoadFailure | null>(null)
  const [creating, setCreating] = useState(false)
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [newRole, setNewRole] = useState<AccountRole>('teacher')
  const [organizationId, setOrganizationId] = useState('')
  const [mutating, setMutating] = useState(false)
  const [actionError, setActionError] = useState('')
  const [notice, setNotice] = useState('')

  const loadAccounts = async (pageOffset = offset, filters: Filters = { search, role: roleFilter, state: stateFilter }) => {
    setLoadState('loading')
    setLoadFailure(null)
    setOffset(pageOffset)
    if (!hasFirebaseAuthBridge()) {
      setAccounts([]); setTotal(0)
      setLoadFailure({ title: 'Chưa có phiên Firebase Authentication', message: 'Cổng Platform Admin đang mở nhưng chưa có Firebase ID token để backend xác minh. Đăng nhập lại bằng tài khoản Platform Admin.', auth: true, denied: false })
      setLoadState('error')
      return
    }
    try {
      const page = await userService.listUsers({ search: filters.search.trim() || undefined, role: filters.role || undefined, state: filters.state || undefined, limit: PAGE_SIZE, offset: pageOffset })
      setAccounts(page.items)
      setTotal(page.total)
      setRoleEdits(Object.fromEntries(page.items.map((account) => [account.account_id, account.role ?? ''])))
      setOrganizationEdits({})
      setLoadState('ready')
    } catch (cause) {
      setAccounts([]); setTotal(0)
      setLoadFailure(toLoadFailure(cause))
      setLoadState('error')
    }
  }

  useEffect(() => {
    void Promise.resolve().then(() => loadAccounts(0, { search: '', role: '', state: '' }))
  }, [])

  const submitFilters = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setHasAppliedFilters(Boolean(search.trim() || roleFilter || stateFilter))
    setActionError(''); setNotice('')
    void loadAccounts(0, { search, role: roleFilter, state: stateFilter })
  }

  const clearFilters = () => {
    setSearch(''); setRoleFilter(''); setStateFilter(''); setHasAppliedFilters(false); setOffset(0); setActionError('')
    void loadAccounts(0, { search: '', role: '', state: '' })
  }

  const createAccount = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (loadState !== 'ready' || !hasFirebaseAuthBridge()) return
    const submittedEmail = email.trim()
    setMutating(true); setActionError(''); setNotice('')
    try {
      await userService.createAccount({ email: submittedEmail, display_name: displayName.trim(), role: newRole, ...(newRole === 'school_manager' ? { organization_id: organizationId.trim() } : {}) })
      setEmail(''); setDisplayName(''); setOrganizationId(''); setCreating(false)
      let sent = true
      try { await authService.resetPassword(submittedEmail) } catch { sent = false }
      setNotice(sent ? 'Đã tạo tài khoản và yêu cầu Firebase gửi email đặt mật khẩu.' : 'Đã tạo tài khoản nhưng chưa gửi được email đặt mật khẩu. Người dùng có thể chọn “Quên mật khẩu” ở màn đăng nhập.')
      setSearch(''); setRoleFilter(''); setStateFilter(''); setHasAppliedFilters(false)
      await loadAccounts(0, { search: '', role: '', state: '' })
    } catch (cause) { setActionError(messageFrom(cause, 'Không tạo được tài khoản.')) }
    finally { setMutating(false) }
  }

  const saveRole = async (account: ManagedAccount) => {
    const role = roleEdits[account.account_id]
    if (!role || role === account.role || loadState !== 'ready' || !hasFirebaseAuthBridge()) return
    const org = role === 'school_manager' ? organizationEdits[account.account_id]?.trim() : undefined
    if (role === 'school_manager' && !org) { setActionError('Nhập mã tổ chức trước khi gán vai trò Quản lý trường.'); return }
    setMutating(true); setActionError(''); setNotice('')
    try {
      await userService.updateAccount(account.account_id, { role, ...(org ? { organization_id: org } : {}) })
      setNotice('Đã cập nhật vai trò. Quyền truy cập lớp vẫn cần phân công riêng bởi School Manager.')
      await loadAccounts()
    } catch (cause) { setActionError(messageFrom(cause, 'Không cập nhật được vai trò.')) }
    finally { setMutating(false) }
  }

  const toggleState = async (account: ManagedAccount) => {
    if (loadState !== 'ready' || !hasFirebaseAuthBridge()) return
    setMutating(true); setActionError(''); setNotice('')
    try {
      await userService.updateAccount(account.account_id, { state: account.state === 'active' ? 'disabled' : 'active' })
      setNotice(account.state === 'active' ? 'Đã khóa tài khoản và thu hồi refresh token.' : 'Đã mở lại tài khoản.')
      await loadAccounts()
    } catch (cause) { setActionError(messageFrom(cause, 'Không đổi được trạng thái tài khoản.')) }
    finally { setMutating(false) }
  }

  const loginAgain = () => { logout(); navigate('/login?role=admin', { replace: true }) }
  const filtersDisabled = loadState !== 'ready' || mutating
  const canManage = loadState === 'ready' && !mutating
  const pages = total ? Math.ceil(total / PAGE_SIZE) : 0
  const currentPage = pages ? Math.floor(offset / PAGE_SIZE) + 1 : 0
  const rangeStart = total ? offset + 1 : 0
  const rangeEnd = Math.min(offset + accounts.length, total)

  return (
    <section className='platform-accounts' aria-labelledby='accounts-title'>
      <header className='accounts-heading'>
        <div className='accounts-heading-copy'>
          <p className='accounts-kicker'><MgIcon name='users' size={18} /> Quản trị nền tảng</p>
          <h1 id='accounts-title'>Tài khoản và vai trò</h1>
          <p className='accounts-description'>Quản lý danh tính và trạng thái truy cập trên Sketch2Life.</p>
          <p className='accounts-scope-note'><span className='accounts-scope-icon' aria-hidden='true'><MgIcon name='shield' size={17} /></span>Vai trò được backend kiểm tra theo từng phạm vi. Teacher cần được phân công lớp; Platform Admin không mặc định xem hồ sơ hay media trẻ.</p>
        </div>
        <div className='accounts-heading-side'>
          <div className='accounts-count-card' aria-live='polite'><span>Kết quả</span><strong>{loadState === 'ready' ? total.toLocaleString('vi-VN') : '—'}</strong><small>{loadState === 'ready' ? 'theo bộ lọc hiện tại' : loadState === 'loading' ? 'đang tải dữ liệu' : 'chưa tải được dữ liệu'}</small></div>
          <button type='button' className='accounts-button accounts-button-primary' disabled={!canManage} onClick={() => { setCreating((value) => !value); setActionError('') }}><MgIcon name={creating ? 'close' : 'plus'} size={18} />{creating ? 'Đóng biểu mẫu' : 'Tạo tài khoản'}</button>
        </div>
      </header>

      {notice && <div className='accounts-feedback is-success' role='status'><span aria-hidden='true'><MgIcon name='check' size={18} /></span><p>{notice}</p></div>}
      {actionError && <div className='accounts-feedback is-error' role='alert'><span aria-hidden='true'><MgIcon name='alert' size={18} /></span><p>{actionError}</p></div>}

      {loadFailure && <section className={`accounts-load-error ${loadFailure.auth ? 'is-warning' : loadFailure.denied ? 'is-denied' : ''}`} role='alert' aria-labelledby='accounts-error-title'>
        <span className='accounts-error-icon' aria-hidden='true'><MgIcon name={loadFailure.auth ? 'lock' : 'alert'} size={22} /></span>
        <div className='accounts-error-copy'><h2 id='accounts-error-title'>{loadFailure.title}</h2><p>{loadFailure.message}</p></div>
        <div className='accounts-error-actions'><button type='button' className='accounts-button accounts-button-secondary' onClick={() => void loadAccounts()} disabled={loadState === 'loading'}><MgIcon name='refresh' size={17} />Thử tải lại</button>{loadFailure.auth && <button type='button' className='accounts-button accounts-button-primary' onClick={loginAgain}>Đăng nhập lại</button>}</div>
      </section>}

      {creating && canManage && <form className='accounts-panel accounts-create-form' onSubmit={(event) => void createAccount(event)} aria-busy={mutating}>
        <div className='accounts-panel-heading'><div><p className='accounts-eyebrow'>Danh tính mới</p><h2>Tạo tài khoản</h2></div><span className='accounts-panel-mark' aria-hidden='true'><MgIcon name='userplus' size={21} /></span></div>
        <div className='accounts-form-grid'>
          <label className='accounts-field'><span>Email tài khoản</span><input required type='email' autoComplete='email' value={email} onChange={(event) => setEmail(event.target.value)} disabled={mutating} /></label>
          <label className='accounts-field'><span>Tên hiển thị</span><input required maxLength={200} autoComplete='name' value={displayName} onChange={(event) => setDisplayName(event.target.value)} disabled={mutating} /></label>
          <label className='accounts-field'><span>Vai trò sản phẩm</span><select value={newRole} onChange={(event) => setNewRole(event.target.value as AccountRole)} disabled={mutating}>{ROLE_OPTIONS.map((role) => <option key={role} value={role}>{ROLE_LABELS[role]}</option>)}</select></label>
          {newRole === 'school_manager' && <label className='accounts-field'><span>Mã tổ chức</span><input required value={organizationId} onChange={(event) => setOrganizationId(event.target.value)} disabled={mutating} /></label>}
        </div>
        <p className='accounts-form-hint'>Tài khoản không có mật khẩu mặc định. Firebase sẽ gửi email đặt mật khẩu; tài khoản Teacher vẫn cần School Manager phân công vào lớp.</p>
        <div className='accounts-form-actions'><button type='button' className='accounts-button accounts-button-secondary' onClick={() => setCreating(false)} disabled={mutating}>Hủy</button><button type='submit' className='accounts-button accounts-button-primary' disabled={mutating}><MgIcon name={mutating ? 'refresh' : 'plus'} size={18} />{mutating ? 'Đang tạo tài khoản…' : 'Tạo tài khoản'}</button></div>
      </form>}

      <form className='accounts-filters accounts-panel' onSubmit={submitFilters} aria-label='Lọc danh sách tài khoản'>
        <label className='accounts-search-field'><span className='accounts-visually-hidden'>Tìm tài khoản theo email hoặc tên hiển thị</span><MgIcon name='search' size={19} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder='Email hoặc tên hiển thị' disabled={filtersDisabled} /></label>
        <label className='accounts-select-field'><span className='accounts-visually-hidden'>Lọc theo vai trò</span><select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value as AccountRole | '')} disabled={filtersDisabled}><option value=''>Tất cả vai trò</option>{ROLE_OPTIONS.map((role) => <option key={role} value={role}>{ROLE_LABELS[role]}</option>)}</select></label>
        <label className='accounts-select-field'><span className='accounts-visually-hidden'>Lọc theo trạng thái tài khoản</span><select value={stateFilter} onChange={(event) => setStateFilter(event.target.value as AccountState | '')} disabled={filtersDisabled}><option value=''>Tất cả trạng thái</option><option value='active'>Đang hoạt động</option><option value='disabled'>Đã khóa</option></select></label>
        <button type='submit' className='accounts-button accounts-button-secondary' disabled={filtersDisabled}>Tìm tài khoản</button>
      </form>

      <section className='accounts-panel accounts-list-panel' aria-labelledby='accounts-list-title' aria-busy={loadState === 'loading'}>
        <div className='accounts-list-heading'><div><p className='accounts-eyebrow'>Danh sách</p><h2 id='accounts-list-title'>Tài khoản người dùng</h2></div>{loadState === 'ready' && <span className='accounts-result-pill'>{total.toLocaleString('vi-VN')} kết quả</span>}</div>
        {loadState === 'loading' && <div className='accounts-list-state' role='status' aria-live='polite'><span className='accounts-spinner' aria-hidden='true' /><p>Đang tải danh sách tài khoản…</p></div>}
        {loadState === 'error' && <div className='accounts-list-state is-error-state'><p>Danh sách đang được ẩn đến khi backend xác nhận dữ liệu.</p></div>}
        {loadState === 'ready' && accounts.length === 0 && <div className='accounts-list-state is-empty-state'><span className='accounts-empty-icon' aria-hidden='true'><MgIcon name={hasAppliedFilters ? 'search' : 'users'} size={25} /></span><h3>{hasAppliedFilters ? 'Không tìm thấy tài khoản phù hợp' : 'Chưa có tài khoản'}</h3><p>{hasAppliedFilters ? 'Thử đổi từ khóa hoặc bộ lọc để tìm tài khoản.' : 'Tài khoản sẽ xuất hiện ở đây sau khi được tạo trong hệ thống.'}</p>{hasAppliedFilters ? <button type='button' className='accounts-button accounts-button-secondary' onClick={clearFilters}>Xóa bộ lọc</button> : <button type='button' className='accounts-button accounts-button-secondary' onClick={() => setCreating(true)} disabled={!canManage}><MgIcon name='plus' size={17} />Tạo tài khoản đầu tiên</button>}</div>}

        {loadState === 'ready' && accounts.length > 0 && <div className='accounts-table-wrap'><table className='accounts-table'><thead><tr><th scope='col'>Tài khoản</th><th scope='col'>Vai trò</th><th scope='col'>Trạng thái</th><th scope='col'>Revision</th><th scope='col'>Thao tác</th></tr></thead><tbody>
          {accounts.map((account) => {
            const role = roleEdits[account.account_id] ?? account.role ?? ''
            const changed = Boolean(role && role !== account.role)
            const needsOrganization = role === 'school_manager' && changed
            const orgValue = organizationEdits[account.account_id] ?? ''
            const label = account.email ?? account.account_id
            return <tr key={account.account_id}>
              <td data-label='Tài khoản'><div className='accounts-person'><span className='accounts-avatar' aria-hidden='true'>{(account.display_name || account.email || '?').trim().slice(0, 1).toLocaleUpperCase('vi-VN')}</span><span className='accounts-person-copy'><strong>{account.display_name || 'Chưa có tên'}</strong><span>{account.email || 'Chưa có email'}</span></span></div></td>
              <td data-label='Vai trò'><div className='accounts-role-editor'><label className='accounts-visually-hidden' htmlFor={`account-role-${account.account_id}`}>Vai trò của {label}</label><select id={`account-role-${account.account_id}`} value={role} onChange={(event) => setRoleEdits((current) => ({ ...current, [account.account_id]: event.target.value as AccountRole | '' }))} disabled={!canManage}><option value=''>Chưa gán vai trò</option>{ROLE_OPTIONS.map((item) => <option key={item} value={item}>{ROLE_LABELS[item]}</option>)}</select>{needsOrganization && <label className='accounts-inline-organization'><span>Mã tổ chức</span><input required aria-label={`Mã tổ chức cho ${label}`} value={orgValue} onChange={(event) => setOrganizationEdits((current) => ({ ...current, [account.account_id]: event.target.value }))} disabled={!canManage} /></label>}</div></td>
              <td data-label='Trạng thái'><span className={`accounts-status ${account.state === 'active' ? 'is-active' : 'is-disabled'}`}><span aria-hidden='true' />{account.state === 'active' ? 'Đang hoạt động' : 'Đã khóa'}</span></td>
              <td data-label='Revision'><span className='accounts-revision'>{account.revision}</span></td>
              <td data-label='Thao tác'><div className='accounts-row-actions'><button type='button' className='accounts-button accounts-button-small accounts-button-outline' disabled={!canManage || !changed || (needsOrganization && !orgValue.trim())} onClick={() => void saveRole(account)}>Lưu vai trò</button><button type='button' className={`accounts-button accounts-button-small ${account.state === 'active' ? 'accounts-button-danger' : 'accounts-button-outline'}`} disabled={!canManage} onClick={() => void toggleState(account)}>{account.state === 'active' ? 'Khóa tài khoản' : 'Mở lại'}</button></div></td>
            </tr>
          })}
        </tbody></table></div>}

        {loadState === 'ready' && accounts.length > 0 && <footer className='accounts-pagination'><p>Đang hiển thị {rangeStart.toLocaleString('vi-VN')}–{rangeEnd.toLocaleString('vi-VN')} trên {total.toLocaleString('vi-VN')} tài khoản.</p><div className='accounts-pagination-controls'><span>Trang {currentPage} / {pages}</span><button type='button' className='accounts-button accounts-button-secondary' disabled={mutating || offset === 0} onClick={() => void loadAccounts(Math.max(0, offset - PAGE_SIZE))}><MgIcon name='arrow-left' size={17} />Trước</button><button type='button' className='accounts-button accounts-button-secondary' disabled={mutating || offset + accounts.length >= total} onClick={() => void loadAccounts(offset + PAGE_SIZE)}>Tiếp<MgIcon name='arrow-right' size={17} /></button></div></footer>}
      </section>

      <p className='accounts-audit-note'><MgIcon name='info' size={17} /><span>Role và trạng thái được quản lý bằng API có xác thực. Quyền nội dung là capability riêng; màn này chưa cấp capability và không mở quyền xem hồ sơ hoặc media trẻ.</span></p>
    </section>
  )
}
