import { parentConfig } from '../config';
import type { ParentUser } from '../../domain/types';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import type { ParentIdentityPort } from '../../application/ports/ParentPorts';

const IDENTITY_TOOLKIT = 'https://identitytoolkit.googleapis.com/v1';
const SECURE_TOKEN = 'https://securetoken.googleapis.com/v1/token';

type FirebasePayload = {
  localId?: string;
  user_id?: string;
  email?: string;
  idToken?: string;
  id_token?: string;
  refreshToken?: string;
  refresh_token?: string;
  expiresIn?: string;
  expires_in?: string;
  error?: { message?: string };
};

type Session = { user: ParentUser; idToken: string; refreshToken: string; expiresAt: number };

const authMessages: Record<string, string> = {
  EMAIL_EXISTS: 'Email này đã được đăng ký.',
  INVALID_EMAIL: 'Email chưa đúng định dạng.',
  INVALID_LOGIN_CREDENTIALS: 'Email hoặc mật khẩu không đúng.',
  EMAIL_NOT_FOUND: 'Email hoặc mật khẩu không đúng.',
  INVALID_PASSWORD: 'Email hoặc mật khẩu không đúng.',
  WEAK_PASSWORD: 'Mật khẩu cần có ít nhất 6 ký tự.',
  TOO_MANY_ATTEMPTS_TRY_LATER: 'Thử lại sau ít phút.',
  ACCOUNT_ROLE_MISMATCH: 'Tài khoản này không có quyền Phụ huynh.',
};

export class ParentAuthError extends ParentApplicationError {
  constructor(code: string, message: string) {
    super(code, message);
    this.name = 'ParentAuthError';
  }
}

export class ParentAuth implements ParentIdentityPort {
  private session: Session | null = null;
  private refreshInFlight: Promise<string> | null = null;

  async currentUser(): Promise<ParentUser | null> {
    return this.session?.user ?? null;
  }

  async signIn(email: string, password: string): Promise<ParentUser> {
    const payload = await this.postFirebase(
      `${IDENTITY_TOOLKIT}/accounts:signInWithPassword?key=${encodeURIComponent(this.apiKey())}`,
      { email: email.trim(), password, returnSecureToken: true },
    );
    this.session = this.toSession(payload);
    try {
      await this.requireParentRole();
      return this.session.user;
    } catch (error) {
      await this.signOut();
      throw error;
    }
  }

  async signUp(email: string, password: string): Promise<ParentUser> {
    const apiBaseUrl = this.apiUrl();
    const registrationUrl = `${apiBaseUrl}/api/auth/v1/registrations`;
    const response = await fetch(registrationUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ email: email.trim(), password }),
    }).catch((error: unknown) => {
      if (__DEV__) {
        console.info('parent_registration_network_failed', {
          origin: new URL(registrationUrl).origin,
          path: '/api/auth/v1/registrations',
          errorName: error instanceof Error ? error.name : 'UnknownError',
          errorMessage: error instanceof Error ? error.message : String(error),
        });
      }
      throw new ParentAuthError('REGISTRATION_NETWORK_ERROR', 'Không kết nối được máy chủ đăng ký.');
    });
    if (__DEV__) {
      console.info('parent_registration_response_received', {
        origin: new URL(registrationUrl).origin,
        path: '/api/auth/v1/registrations',
        status: response.status,
      });
    }
    const result = await response.json().catch(() => ({})) as {
      status?: string;
      role?: string;
      code?: string;
      detail?: { code?: string };
    };
    if (!response.ok || result.status !== 'IDENTITY_CREATED' || result.role !== 'parent') {
      const code = result.code ?? result.detail?.code ?? `REGISTRATION_HTTP_${response.status}`;
      throw new ParentAuthError(code, authMessages[code] ?? 'Không thể tạo tài khoản lúc này.');
    }
    return this.signIn(email, password);
  }

  async signInWithGoogle(googleIdToken: string): Promise<ParentUser> {
    if (!googleIdToken.trim()) {
      throw new ParentAuthError('GOOGLE_TOKEN_MISSING', 'Google chưa trả về mã xác thực.');
    }
    const body = await this.postFirebase(
      `${IDENTITY_TOOLKIT}/accounts:signInWithIdp?key=${encodeURIComponent(this.apiKey())}`,
      {
        postBody: `id_token=${encodeURIComponent(googleIdToken)}&providerId=google.com`,
        requestUri: 'http://localhost',
        returnIdpCredential: true,
        returnSecureToken: true,
      },
    );
    this.session = this.toSession(body);
    try {
      await this.requireParentRole();
      return this.session.user;
    } catch (error) {
      await this.signOut();
      throw error;
    }
  }

  async resetPassword(email: string): Promise<void> {
    try {
      await this.postFirebase(
        `${IDENTITY_TOOLKIT}/accounts:sendOobCode?key=${encodeURIComponent(this.apiKey())}`,
        { requestType: 'PASSWORD_RESET', email: email.trim() },
      );
    } catch (error) {
      if (error instanceof ParentAuthError && ['EMAIL_NOT_FOUND', 'USER_NOT_FOUND'].includes(error.code)) return;
      throw error;
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    const current = this.session?.user;
    if (!current?.email) throw new ParentAuthError('AUTH_REQUIRED', 'Đăng nhập lại để đổi mật khẩu.');
    const verifiedUser = await this.signIn(current.email, currentPassword);
    if (verifiedUser.subject !== current.subject) {
      await this.signOut();
      throw new ParentAuthError('REAUTHENTICATION_FAILED', 'Không xác minh được tài khoản hiện tại.');
    }
    const payload = await this.postFirebase(
      `${IDENTITY_TOOLKIT}/accounts:update?key=${encodeURIComponent(this.apiKey())}`,
      { idToken: await this.getIdToken(), password: newPassword, returnSecureToken: true },
    );
    this.session = this.toSession(payload, current);
  }

  async getIdToken(): Promise<string> {
    const active = this.session;
    if (!active) throw new Error('Đăng nhập để tiếp tục.');
    if (active.expiresAt > Date.now() + 60_000) return active.idToken;
    if (!this.refreshInFlight) this.refreshInFlight = this.refresh(active);
    try {
      return await this.refreshInFlight;
    } finally {
      this.refreshInFlight = null;
    }
  }

  async signOut(): Promise<void> {
    this.session = null;
    this.refreshInFlight = null;
  }

  private async requireParentRole(): Promise<void> {
    const response = await fetch(`${this.apiUrl()}/api/auth/v1/me`, {
      headers: { Authorization: `Bearer ${await this.getIdToken()}`, Accept: 'application/json' },
    }).catch(() => { throw new ParentAuthError('AUTH_API_UNAVAILABLE', 'Không kiểm tra được quyền tài khoản.'); });
    const body = await response.json().catch(() => ({})) as {
      code?: string;
      role?: string;
      state?: string;
      detail?: { code?: string };
    };
    if (!response.ok) {
      const code = body.code ?? body.detail?.code ?? `AUTH_API_HTTP_${response.status}`;
      if (__DEV__) {
        console.info('parent_role_resolution_failed', {
          status: response.status,
          code,
          responseKeys: Object.keys(body),
        });
      }
      if (response.status === 401) {
        throw new ParentAuthError(code, 'Phiên đăng nhập không hợp lệ. Đăng nhập lại để tiếp tục.');
      }
      if (response.status === 403) {
        throw new ParentAuthError(
          code,
          'Tài khoản chưa được thiết lập quyền trong Sketch2Life. Hãy liên hệ quản trị viên.',
        );
      }
      throw new ParentAuthError(code, 'Không kiểm tra được quyền tài khoản. Thử lại sau.');
    }
    if (body.role !== 'parent' || body.state !== 'active') {
      throw new ParentAuthError('ACCOUNT_ROLE_MISMATCH', authMessages.ACCOUNT_ROLE_MISMATCH);
    }
  }

  private async refresh(active: Session): Promise<string> {
    const response = await fetch(`${SECURE_TOKEN}?key=${encodeURIComponent(this.apiKey())}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `grant_type=refresh_token&refresh_token=${encodeURIComponent(active.refreshToken)}`,
    });
    const payload = await this.readFirebase(response);
    this.session = this.toSession(payload, active.user);
    return this.session.idToken;
  }

  private apiKey(): string {
    if (!parentConfig.firebaseApiKey) throw new Error('Thiếu Firebase API key trong .env gốc.');
    return parentConfig.firebaseApiKey;
  }

  private apiUrl(): string {
    if (!parentConfig.apiBaseUrl) throw new Error('Thiếu API URL trong .env gốc.');
    return parentConfig.apiBaseUrl;
  }

  private toSession(payload: FirebasePayload, previousUser?: ParentUser): Session {
    const subject = payload.localId ?? payload.user_id ?? previousUser?.subject;
    const idToken = payload.idToken ?? payload.id_token;
    const refreshToken = payload.refreshToken ?? payload.refresh_token;
    const expiresIn = Number(payload.expiresIn ?? payload.expires_in ?? '3600');
    if (!subject || !idToken || !refreshToken || !Number.isFinite(expiresIn) || expiresIn <= 0) {
      throw new ParentAuthError('INVALID_AUTH_RESPONSE', 'Firebase trả về phiên đăng nhập không hợp lệ.');
    }
    const user: ParentUser = { subject, email: payload.email ?? previousUser?.email ?? '', role: 'parent' };
    return { user, idToken, refreshToken, expiresAt: Date.now() + expiresIn * 1000 };
  }

  private async postFirebase(url: string, body: object): Promise<FirebasePayload> {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).catch(() => { throw new ParentAuthError('AUTH_NETWORK_ERROR', 'Không kết nối được Firebase Auth.'); });
    return this.readFirebase(response);
  }

  private async readFirebase(response: Response): Promise<FirebasePayload> {
    const body = await response.json().catch(() => ({})) as FirebasePayload;
    if (!response.ok) {
      const code = body.error?.message ?? 'FIREBASE_AUTH_ERROR';
      throw new ParentAuthError(code, authMessages[code] ?? 'Không thể xác thực lúc này.');
    }
    return body;
  }
}
