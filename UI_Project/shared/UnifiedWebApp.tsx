import React, { useEffect, useRef, useState } from 'react';
import { BrandMark } from './BrandMark';
import { Workspace, type Role } from './webWorkspace';
import { backendMessage, isLocalPreview, signInAndResolveRole, type PortalRole } from './backendApi';

const roleContent: Record<Role, { label: string; detail: string; mark: string; apiRole: PortalRole }> = {
  teacher: { label: 'Giáo viên', detail: 'Giáo án, lớp và buổi học', mark: '01', apiRole: 'teacher' },
  manager: { label: 'Quản lý trường', detail: 'Lớp, phân công và gói dịch vụ', mark: '02', apiRole: 'school_manager' },
  admin: { label: 'Quản trị nền tảng', detail: 'Nội dung và vận hành', mark: '03', apiRole: 'platform_admin' },
};

type AuthPage = 'login' | 'register' | 'recover';

type ActivationStage = 'invite' | 'credentials' | 'verify' | 'complete';
type InvitationPreviewScenario = 'valid' | 'invalid' | 'expired' | 'used';

function InvitationActivationFlow({onBack}: {onBack: () => void}) {
  const [stage, setStage] = useState<ActivationStage>('invite');
  const [scenario, setScenario] = useState<InvitationPreviewScenario>('valid');
  const [inviteRole, setInviteRole] = useState<'teacher' | 'manager'>('teacher');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');

  const checkInvite = (event: React.FormEvent): void => {
    event.preventDefault();
    setError('');
    if (!fullName.trim() || !email.trim() || !inviteCode.trim()) return;
    if (scenario !== 'valid') {
      setError(scenario === 'expired'
        ? 'Lời mời đã hết hạn theo trạng thái minh họa. Liên hệ Quản lý trường để được gửi lại; hệ thống không tiết lộ tài khoản khác.'
        : scenario === 'used'
          ? 'Lời mời đã được sử dụng theo trạng thái minh họa. Hãy đăng nhập hoặc dùng khôi phục tài khoản.'
          : 'Không thể xác minh lời mời hoặc email trong trạng thái minh họa. Kiểm tra lại thông tin hoặc hỏi Quản lý trường.');
      return;
    }
    const expectedInvite = inviteRole === 'teacher'
      ? {name: 'Giáo viên minh họa', email: 'teacher.demo@example.test', code: 'S2L-DEMO-TEACHER'}
      : {name: 'Quản lý trường minh họa', email: 'manager.demo@example.test', code: 'S2L-DEMO-MANAGER'};
    if (fullName.trim() !== expectedInvite.name || email.trim().toLocaleLowerCase('vi') !== expectedInvite.email || inviteCode.trim() !== expectedInvite.code) {
      setError('Thông tin chưa khớp lời mời fixture. Dùng lời mời mẫu tương ứng để xem tiếp luồng preview.');
      return;
    }
    setStage('credentials');
  };
  const saveCredentials = (event: React.FormEvent): void => {
    event.preventDefault();
    setError('');
    if (!password || !confirmPassword) { setError('Nhập mật khẩu và xác nhận để xem bước tiếp theo.'); return; }
    if (password !== confirmPassword) { setError('Hai mật khẩu chưa khớp. Kiểm tra lại trước khi tiếp tục.'); return; }
    setStage('verify');
  };
  const verifyEmail = (event: React.FormEvent): void => {
    event.preventDefault();
    if (verificationCode.trim() !== '246810') { setError('Mã minh họa chưa đúng. Dùng 246810 để xem nhánh thành công; không có email thật được gửi.'); return; }
    setError('');
    setPassword('');
    setConfirmPassword('');
    setStage('complete');
  };
  const useDemoInvite = (): void => {
    setFullName(inviteRole === 'teacher' ? 'Giáo viên minh họa' : 'Quản lý trường minh họa');
    setEmail(inviteRole === 'teacher' ? 'teacher.demo@example.test' : 'manager.demo@example.test');
    setInviteCode(inviteRole === 'teacher' ? 'S2L-DEMO-TEACHER' : 'S2L-DEMO-MANAGER');
  };
  return <section className="activation-flow" aria-labelledby="activation-flow-title">
    <div className="activation-progress" aria-label={`Bước ${stage === 'invite' ? 1 : stage === 'credentials' ? 2 : stage === 'verify' ? 3 : 4} trên 4`}>
      {(['invite', 'credentials', 'verify', 'complete'] as const).map((step, index) => <span key={step} className={stage === step ? 'is-current' : ['invite', 'credentials', 'verify', 'complete'].indexOf(stage) > index ? 'is-done' : ''}>{index + 1}</span>)}
    </div>
    <div className="activation-stage-heading"><span className="flow-eyebrow">{stage === 'invite' ? 'BƯỚC 1 · LỜI MỜI' : stage === 'credentials' ? 'BƯỚC 2 · THÔNG TIN ĐĂNG NHẬP' : stage === 'verify' ? 'BƯỚC 3 · XÁC MINH EMAIL' : 'BƯỚC 4 · HOÀN TẤT'}</span><h3 id="activation-flow-title">{stage === 'invite' ? 'Kiểm tra lời mời' : stage === 'credentials' ? 'Tạo thông tin đăng nhập' : stage === 'verify' ? 'Xác minh địa chỉ email' : 'Kích hoạt mẫu hoàn tất'}</h3><p>{stage === 'invite' ? 'Vai trò và tổ chức phải lấy từ lời mời đã được server xác minh.' : stage === 'credentials' ? 'Chỉ thiết lập cho luồng mời hợp lệ; không tự chọn hoặc nâng quyền.' : stage === 'verify' ? `Bản thật gửi link xác minh; preview dùng mã minh họa cho ${email}.` : 'Identity và quyền thật chưa được tạo.'}</p></div>
    {stage === 'invite' ? <form className="activation-form" onSubmit={checkInvite}>
      <label>Tên đầy đủ<input autoComplete="name" value={fullName} onChange={(event) => setFullName(event.target.value)} required maxLength={100}/></label>
      <label>Email được mời<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="ten@truong.edu.vn"/></label>
      <label>Mã mời<input value={inviteCode} onChange={(event) => setInviteCode(event.target.value)} required autoComplete="off" placeholder="Nhập mã từ tổ chức"/></label>
      <label>Lời mời mẫu<select value={inviteRole} onChange={(event) => { setInviteRole(event.target.value as 'teacher' | 'manager'); setError(''); setFullName(''); setEmail(''); setInviteCode(''); }}><option value="teacher">Giáo viên · fixture</option><option value="manager">Quản lý trường · fixture</option></select></label>
      <label>Kết quả kiểm tra minh họa<select value={scenario} onChange={(event) => { setScenario(event.target.value as InvitationPreviewScenario); setError(''); }}><option value="valid">Lời mời còn hiệu lực</option><option value="invalid">Không khớp / không tồn tại</option><option value="expired">Lời mời hết hạn</option><option value="used">Lời mời đã dùng</option></select></label>
      <div className="activation-demo-note"><strong>Demo invitation</strong><span>Không dùng tài khoản thật. Bấm để điền dữ liệu tổng hợp vào biểu mẫu.</span><button type="button" className="unified-auth-link" onClick={useDemoInvite}>Dùng lời mời mẫu</button></div>
      {error ? <p className="unified-auth-error" role="alert">{error}</p> : null}
      <button type="submit" className="unified-auth-submit">Kiểm tra lời mời <span aria-hidden="true">→</span></button>
    </form> : null}
    {stage === 'credentials' ? <form className="activation-form" onSubmit={saveCredentials}>
      <div className="activation-invite-result"><strong>{inviteRole === 'teacher' ? 'Giáo viên' : 'Quản lý trường'} · Tổ chức minh họa</strong><span>Email khớp lời mời fixture · chưa xác minh thật</span></div>
      <label>Mật khẩu mới<input type="password" autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} required/></label>
      <label>Nhập lại mật khẩu<input type="password" autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required/></label>
      <p className="unified-auth-note">Mật khẩu chỉ tồn tại trong bộ nhớ preview và sẽ bị xóa khi hoàn tất/thoát. Quy tắc mật khẩu thật do identity provider áp dụng.</p>
      {error ? <p className="unified-auth-error" role="alert">{error}</p> : null}
      <div className="activation-actions"><button type="button" className="unified-auth-link" onClick={() => { setStage('invite'); setError(''); }}>Quay lại lời mời</button><button type="submit" className="unified-auth-submit">Tiếp tục xác minh <span aria-hidden="true">→</span></button></div>
    </form> : null}
    {stage === 'verify' ? <form className="activation-form" onSubmit={verifyEmail}>
      <div className="activation-invite-result"><strong>Đang chờ xác minh</strong><span>Trạng thái thật phụ thuộc Firebase Authentication và email adapter.</span></div>
      <label>Mã xác minh demo<input inputMode="numeric" autoComplete="one-time-code" value={verificationCode} onChange={(event) => setVerificationCode(event.target.value)} required placeholder="246810"/></label>
      <p className="unified-auth-note">Mã xem thử: <strong>246810</strong>. Không có email hoặc action link thật được phát đi.</p>
      {error ? <p className="unified-auth-error" role="alert">{error}</p> : null}
      <div className="activation-actions"><button type="button" className="unified-auth-link" onClick={() => { setStage('credentials'); setError(''); }}>Quay lại thông tin</button><button type="submit" className="unified-auth-submit">Xác minh · preview <span aria-hidden="true">→</span></button></div>
    </form> : null}
    {stage === 'complete' ? <div className="activation-complete" role="status"><span aria-hidden="true">✓</span><strong>Đã hoàn tất luồng mẫu</strong><p>Lời mời, email và tài khoản chưa được kiểm tra hoặc tạo bởi server. Đăng nhập thật chỉ khả dụng sau khi identity và role được xác minh.</p><button type="button" className="unified-auth-submit" onClick={onBack}>Quay lại đăng nhập</button></div> : null}
  </section>;
}

export function UnifiedWebApp() {
  const preview = isLocalPreview();
  const [role, setRole] = useState<Role | null>(() => {
    if (!isLocalPreview()) return null;
    const stored = window.sessionStorage.getItem('sketch2life-preview-role');
    return stored === 'teacher' || stored === 'manager' || stored === 'admin' ? stored : null;
  });
  const [page, setPage] = useState<AuthPage>('login');
  const [chosenRole, setChosenRole] = useState<Role>('teacher');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [inviteCode, setInviteCode] = useState('');
  const [name, setName] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const errorSummaryRef = useRef<HTMLDivElement>(null);
  useEffect(() => { if (error) errorSummaryRef.current?.focus(); }, [error]);
  const [confirmation, setConfirmation] = useState('');

  const enterPreview = (nextRole: Role) => {
    window.sessionStorage.setItem('sketch2life-preview-role', nextRole);
    window.location.hash = 'home';
    setRole(nextRole);
  };
  const leave = async () => {
    if (!preview) await window.sketch2lifeAuth?.signOut?.().catch(() => undefined);
    window.sessionStorage.removeItem('sketch2life-preview-role');
    window.location.hash = 'login';
    setRole(null);
    setPassword('');
    setError('');
    setPage('login');
  };
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setConfirmation('');
    if (page === 'recover') {
      setConfirmation(preview ? 'Đây là bản xem trước. Email khôi phục chưa được gửi.' : 'Khôi phục tài khoản cần kết nối Firebase Authentication và luồng xác minh do dự án cấu hình.');
      return;
    }
    if (page === 'register') {
      if (chosenRole === 'admin') { setError('Quyền quản trị nền tảng phải được cấp bởi hệ thống; không thể tự đăng ký.'); return; }
      if (!inviteCode.trim()) { setError('Vui lòng nhập mã mời hoặc thông tin kích hoạt từ tổ chức.'); return; }
      setConfirmation(preview ? 'Biểu mẫu đã được kiểm tra trong bản xem trước. Tài khoản chưa được tạo hoặc gửi đi.' : 'Quy trình mời và kích hoạt tài khoản cần được BE xác nhận trước khi gửi biểu mẫu.');
      return;
    }
    if (preview) { setError('Bản xem trước không xác thực email/mật khẩu. Chọn một vai trò ở bên trái để xem giao diện.'); return; }
    setPending(true);
    try {
      await signInAndResolveRole(roleContent[chosenRole].apiRole, email.trim(), password);
      window.location.hash = 'home';
      setRole(chosenRole);
    } catch (cause) {
      setError(backendMessage(cause));
    } finally {
      setPending(false);
    }
  };

  if (role) return <Workspace key={role} role={role} onLogout={() => void leave()}/>;

  return <main className="unified-auth"><div className="unified-auth-shell"><section className="unified-auth-story" aria-labelledby="auth-story-title"><div className="unified-auth-brand"><BrandMark size={48}/><span><strong>Sketch<span>2</span>Life</strong><small>Một cổng web cho nhà trường</small></span></div><div className="unified-auth-art" aria-hidden="true"><span className="unified-art-sheet unified-art-sheet--back"/><span className="unified-art-sheet unified-art-sheet--front"><i/><i/><i/></span><span className="unified-art-sun"/></div><span className="unified-auth-kicker">KHÔNG GIAN LÀM VIỆC</span><h1 id="auth-story-title">Mỗi vai trò, một góc nhìn rõ ràng.</h1><p>Giáo viên, nhà trường và đội vận hành cùng bắt đầu tại đây.</p><div className="unified-role-list" aria-label="Chọn vai trò xem thử">{(Object.keys(roleContent) as Role[]).map((item) => <button key={item} type="button" className={chosenRole === item ? 'is-selected' : ''} onClick={() => { setChosenRole(item); setError(''); }}><span>{roleContent[item].mark}</span><span><strong>{roleContent[item].label}</strong><small>{roleContent[item].detail}</small></span><b aria-hidden="true">↗</b></button>)}</div>{preview && <div className="unified-preview-actions"><span>Bản xem trước · không dùng tài khoản thật</span><button type="button" onClick={() => enterPreview(chosenRole)}>Xem thử {roleContent[chosenRole].label}<span aria-hidden="true">→</span></button></div>}</section><section className="unified-auth-form-wrap"><div className="unified-auth-switch" role="tablist" aria-label="Tài khoản web"><button role="tab" aria-selected={page === 'login'} className={page === 'login' ? 'active' : ''} onClick={() => { setPage('login'); setError(''); setConfirmation(''); }}>Đăng nhập</button><button role="tab" aria-selected={page === 'register'} className={page === 'register' ? 'active' : ''} onClick={() => { setPage('register'); setError(''); setConfirmation(''); }}>Kích hoạt tài khoản</button></div><div className="unified-auth-heading"><span>{page === 'login' ? 'CHÀO MỪNG TRỞ LẠI' : page === 'register' ? 'BẮT ĐẦU CÙNG SKETCH2LIFE' : 'KHÔI PHỤC TÀI KHOẢN'}</span><h2>{page === 'login' ? 'Đăng nhập cổng web' : page === 'register' ? 'Kích hoạt tài khoản' : 'Lấy lại quyền truy cập'}</h2><p>{page === 'login' ? 'Vai trò được kiểm tra với quyền do backend cấp.' : page === 'register' ? 'Tài khoản nhà trường cần lời mời từ tổ chức.' : 'Nhập email đã dùng cho tài khoản của bạn.'}</p></div>{page === 'register' ? <InvitationActivationFlow onBack={() => { setPage('login'); setError(''); setConfirmation(''); }}/> : <form onSubmit={(event) => void submit(event)} className="unified-auth-form">{page === 'register' && <label>Họ và tên<input value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" required placeholder="Tên người phụ trách"/></label>}<label>Email công việc<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required placeholder="ten@truong.edu.vn"/></label>{page !== 'recover' && <label>Vai trò được cấp<select value={chosenRole} onChange={(event) => setChosenRole(event.target.value as Role)}><option value="teacher">Giáo viên</option><option value="manager">Quản lý trường</option><option value="admin">Quản trị nền tảng</option></select></label>}{page === 'register' && chosenRole !== 'admin' && <label>Mã mời từ tổ chức<input value={inviteCode} onChange={(event) => setInviteCode(event.target.value)} autoComplete="off" placeholder="Nhập mã mời"/></label>}{page === 'login' && <label>Mật khẩu<span className="unified-password"><input type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required placeholder="Nhập mật khẩu"/><button type="button" onClick={() => setShowPassword((current) => !current)} aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}>{showPassword ? 'Ẩn' : 'Hiện'}</button></span></label>}{page === 'register' && chosenRole === 'admin' && <p className="unified-auth-note">Quản trị nền tảng được cấp quyền nội bộ; không có luồng tự đăng ký.</p>}{error && <div ref={errorSummaryRef} tabIndex={-1} className="unified-auth-error" role="alert"><strong>Chưa thể tiếp tục</strong><span>{error}</span></div>}{confirmation && <p className="unified-auth-confirm" role="status">{confirmation}</p>}<button type="submit" className="unified-auth-submit" disabled={pending}>{pending ? 'Đang xác minh…' : page === 'login' ? 'Đăng nhập' : page === 'register' ? 'Kiểm tra thông tin kích hoạt' : 'Tiếp tục khôi phục'}<span aria-hidden="true">→</span></button>{page === 'login' ? <button type="button" className="unified-auth-link" onClick={() => { setPage('recover'); setError(''); }}>Quên mật khẩu?</button> : <button type="button" className="unified-auth-link" onClick={() => { setPage('login'); setError(''); setConfirmation(''); }}>Quay lại đăng nhập</button>}</form>}<p className="unified-auth-foot">© Sketch2Life · Quyền truy cập và dữ liệu được kiểm tra theo vai trò.</p></section></div></main>;
}
