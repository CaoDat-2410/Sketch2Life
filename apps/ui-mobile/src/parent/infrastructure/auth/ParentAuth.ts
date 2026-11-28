import { parentConfig } from '../config';
import type { ParentUser } from '../../domain/types';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import type { ParentIdentityPort } from '../../application/ports/ParentPorts';

const IDENTITY_TOOLKIT = 'https://identitytoolkit.googleapis.com/v1';
const SECURE_TOKEN = 'https://securetoken.googleapis.com/v1/token';

function isFirebaseAuthEmulatorActive(): boolean {
  return typeof __DEV__ !== 'undefined' && __DEV__ && Boolean(parentConfig.firebaseAuthEmulatorUrl);
}

function identityToolkitBaseUrl(): string {
  return isFirebaseAuthEmulatorActive()
    ? `${parentConfig.firebaseAuthEmulatorUrl.replace(/\/+$/, '')}/identitytoolkit.googleapis.com/v1`
    : IDENTITY_TOOLKIT;
}

function secureTokenBaseUrl(): string {
  return isFirebaseAuthEmulatorActive()
    ? `${parentConfig.firebaseAuthEmulatorUrl.replace(/\/+$/, '')}/securetoken.googleapis.com/v1/token`
    : SECURE_TOKEN;
}

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
  RATE_LIMITED: 'Thử lại sau ít phút.',
  PASSWORD_RECOVERY_UNAVAILABLE: 'Chưa gửi được yêu cầu, hãy thử lại sau.',
  ACCOUNT_ROLE_MISMATCH: 'Tài khoản này không có quyền Phụ huynh.',
  ACCOUNT_SETUP_UNAVAILABLE: 'Chưa thể hoàn tất thiết lập tài khoản lúc này. Hãy thử lại sau.',
  DATABASE_UNAVAILABLE: 'Chưa thể tạo tài khoản lúc này. Hãy thử lại sau.',
  IDENTITY_PROVIDER_UNAVAILABLE: 'Chưa thể xác thực tài khoản lúc này. Hãy thử lại sau.',
  FIREBASE_API_KEY_MISSING: 'Ứng dụng chưa sẵn sàng. Hãy thử lại sau.',
  MOBILE_API_URL_MISSING: 'Ứng dụng chưa sẵn sàng. Hãy thử lại sau.',
  REGISTRATION_CREATED_SIGNIN_FAILED: 'Tài khoản đã được tạo nhưng chưa đăng nhập được. Hãy chọn Đăng nhập để tiếp tục; đừng tạo tài khoản mới.',
};

export class ParentAuthError extends ParentApplicationError {
  diagnosticStage?: string;

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
    if (__DEV__) console.info('parent_auth_stage_started', { stage: 'firebase_password_sign_in' });
    let payload: FirebasePayload;
    try {
      payload = await this.postFirebase(
        `${identityToolkitBaseUrl()}/accounts:signInWithPassword?key=${encodeURIComponent(this.apiKey())}`,
        { email: email.trim(), password, returnSecureToken: true },
      );
      if (__DEV__) console.info('parent_auth_stage_succeeded', { stage: 'firebase_password_sign_in' });
    } catch (error: unknown) {
      this.logAuthFailure('firebase_password_sign_in', error);
      if (error instanceof ParentAuthError && !error.diagnosticStage) error.diagnosticStage = 'firebase_password_sign_in';
      throw error;
    }
    this.session = this.toSession(payload);
    try {
      if (__DEV__) console.info('parent_auth_stage_started', { stage: 'backend_parent_scope' });
      await this.ensureParentScope();
      if (__DEV__) console.info('parent_auth_stage_succeeded', { stage: 'backend_parent_scope' });
      return this.session.user;
    } catch (error) {
      this.logAuthFailure('backend_parent_scope', error);
      if (error instanceof ParentAuthError && !error.diagnosticStage) error.diagnosticStage = 'backend_parent_scope';
      await this.signOut();
      throw error;
    }
  }

  async signUp(email: string, password: string): Promise<ParentUser> {
    const apiBaseUrl = this.apiUrl();
    const registrationUrl = `${apiBaseUrl}/api/auth/v1/registrations`;
    let response: Response;
    try {
      response = await fetch(registrationUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ email: email.trim(), password }),
      });
    } catch (error: unknown) {
      if (__DEV__) {
        console.info('parent_registration_network_failed', {
          origin: new URL(registrationUrl).origin,
          path: '/api/auth/v1/registrations',
          errorName: error instanceof Error ? error.name : 'UnknownError',
        });
      }
      const registrationError = new ParentAuthError('REGISTRATION_NETWORK_ERROR', 'Không kết nối được máy chủ đăng ký.');
      const recovered = await this.tryRecoverParentSession(email, password);
      if (recovered) return recovered;
      throw registrationError;
    }
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
      const registrationError = new ParentAuthError(code, authMessages[code] ?? 'Không thể tạo tài khoản lúc này.');
      if ([409, 503].includes(response.status)) {
        const recovered = await this.tryRecoverParentSession(email, password);
        if (recovered) return recovered;
      }
      throw registrationError;
    }
    try {
      return await this.signIn(email, password);
    } catch (error) {
      if (error instanceof ParentAuthError && error.code === 'ACCOUNT_ROLE_MISMATCH') throw error;
      throw new ParentAuthError(
        'REGISTRATION_CREATED_SIGNIN_FAILED',
        authMessages.REGISTRATION_CREATED_SIGNIN_FAILED,
      );
    }
  }

  async signInWithGoogle(googleIdToken: string): Promise<ParentUser> {
    if (!googleIdToken.trim()) {
      throw new ParentAuthError('GOOGLE_TOKEN_MISSING', 'Chưa nhận được thông tin đăng nhập. Hãy thử lại.');
    }
    const body = await this.postFirebase(
      `${identityToolkitBaseUrl()}/accounts:signInWithIdp?key=${encodeURIComponent(this.apiKey())}`,
      {
        postBody: `id_token=${encodeURIComponent(googleIdToken)}&providerId=google.com`,
        requestUri: 'http://localhost',
        returnIdpCredential: true,
        returnSecureToken: true,
      },
    );
    this.session = this.toSession(body);
    try {
      await this.ensureParentScope();
      return this.session.user;
    } catch (error) {
      await this.signOut();
      throw error;
    }
  }

  async resetPassword(email: string): Promise<void> {
    const normalizedEmail = email.trim();
    if (
      normalizedEmail.length < 3
      || normalizedEmail.length > 254
      || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)
    ) {
      throw new ParentAuthError('INVALID_EMAIL', authMessages.INVALID_EMAIL);
    }

    const recoveryUrl = `${this.apiUrl()}/api/auth/v1/password-recovery`;
    let response: Response;
    try {
      // Recovery delivery depends on the backend email worker.
      response = await fetch(recoveryUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: normalizedEmail }),
      });
    } catch {
      if (__DEV__) {
        console.info('parent_password_recovery_failed', {
          status: null,
          code: 'PASSWORD_RECOVERY_UNAVAILABLE',
        });
      }
      throw new ParentAuthError(
        'PASSWORD_RECOVERY_UNAVAILABLE',
        authMessages.PASSWORD_RECOVERY_UNAVAILABLE,
      );
    }

    if (response.status === 202) {
      const result = await response.json().catch(() => ({})) as { status?: string } | null;
      if (result?.status === 'RECOVERY_REQUESTED') return;
      if (__DEV__) {
        console.info('parent_password_recovery_failed', {
          status: response.status,
          code: 'PASSWORD_RECOVERY_UNAVAILABLE',
        });
      }
    } else if (response.status === 429) {
      if (__DEV__) {
        console.info('parent_password_recovery_failed', {
          status: response.status,
          code: 'RATE_LIMITED',
        });
      }
      throw new ParentAuthError('RATE_LIMITED', authMessages.RATE_LIMITED);
    } else if (response.status === 422) {
      if (__DEV__) {
        console.info('parent_password_recovery_failed', {
          status: response.status,
          code: 'INVALID_EMAIL',
        });
      }
      throw new ParentAuthError('INVALID_EMAIL', authMessages.INVALID_EMAIL);
    } else if (__DEV__) {
      console.info('parent_password_recovery_failed', {
        status: response.status,
        code: 'PASSWORD_RECOVERY_UNAVAILABLE',
      });
    }

    throw new ParentAuthError(
      'PASSWORD_RECOVERY_UNAVAILABLE',
      authMessages.PASSWORD_RECOVERY_UNAVAILABLE,
    );
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
      `${identityToolkitBaseUrl()}/accounts:update?key=${encodeURIComponent(this.apiKey())}`,
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
    const url = `${this.apiUrl()}/api/auth/v1/me`;
    if (__DEV__) {
      console.info('parent_auth_backend_request_started', {
        origin: new URL(url).origin,
        path: '/api/auth/v1/me',
      });
    }
    const response = await fetch(url, {
      headers: { Authorization: `Bearer ${await this.getIdToken()}`, Accept: 'application/json' },
    }).catch(() => {
      const error = new ParentAuthError('AUTH_API_UNAVAILABLE', 'Không kiểm tra được quyền tài khoản.');
      error.diagnosticStage = `backend_me_network@${new URL(url).origin}`;
      throw error;
    });
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
          responseKeys: Object.keys(body),
        });
      }
      if (response.status === 401) {
        const error = new ParentAuthError(code, 'Phiên đăng nhập không hợp lệ. Đăng nhập lại để tiếp tục.');
        error.diagnosticStage = `backend_me_401@${new URL(url).origin}`;
        throw error;
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

  private async ensureParentScope(): Promise<void> {
    let initialSetupError: unknown;
    try {
      await this.requireParentRole();
      return;
    } catch (error) {
      if (!(error instanceof ParentAuthError) || error.code !== 'ACCOUNT_SETUP_UNAVAILABLE') throw error;
      initialSetupError = error;
    }

    try {
      await this.completeParentRegistration();
    } catch (error) {
      // Keep the existing generic sign-in message when the backend feature is off.
      if (error instanceof ParentAuthError && error.code === 'ACCOUNT_SETUP_UNAVAILABLE') {
        throw initialSetupError;
      }
      throw error;
    }
    await this.requireParentRole();
  }

  private async completeParentRegistration(): Promise<void> {
    const url = `${this.apiUrl()}/api/auth/v1/registrations/complete`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${await this.getIdToken()}`,
        Accept: 'application/json',
      },
    }).catch(() => {
      const error = new ParentAuthError('AUTH_API_UNAVAILABLE', 'Không kết nối được máy chủ tài khoản.');
      error.diagnosticStage = `backend_registration_complete_network@${new URL(url).origin}`;
      throw error;
    });
    const body = await response.json().catch(() => ({})) as {
      role?: string;
      state?: string;
      code?: string;
      detail?: { code?: string };
    };
    if (!response.ok) {
      const code = body.code ?? body.detail?.code ?? `AUTH_API_HTTP_${response.status}`;
      const error = new ParentAuthError(code, authMessages[code] ?? 'Chưa thể đồng bộ tài khoản với máy chủ.');
      error.diagnosticStage = `backend_registration_complete_${response.status}@${new URL(url).origin}`;
      throw error;
    }
    if (body.role !== 'parent' || body.state !== 'active') {
      throw new ParentAuthError('ACCOUNT_SETUP_UNAVAILABLE', authMessages.ACCOUNT_SETUP_UNAVAILABLE);
    }
  }

  private async tryRecoverParentSession(email: string, password: string): Promise<ParentUser | null> {
    try {
      return await this.signIn(email, password);
    } catch {
      // Keep the original registration response. The login attempt only recovers a
      // Firebase identity whose backend commit succeeded or can now be completed.
      return null;
    }
  }

  private async refresh(active: Session): Promise<string> {
    const response = await fetch(`${secureTokenBaseUrl()}?key=${encodeURIComponent(this.apiKey())}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `grant_type=refresh_token&refresh_token=${encodeURIComponent(active.refreshToken)}`,
    });
    const payload = await this.readFirebase(response);
    this.session = this.toSession(payload, active.user);
    return this.session.idToken;
  }

  private apiKey(): string {
    if (!parentConfig.firebaseApiKey && !isFirebaseAuthEmulatorActive()) {
      throw new ParentAuthError('FIREBASE_API_KEY_MISSING', authMessages.FIREBASE_API_KEY_MISSING);
    }
    return parentConfig.firebaseApiKey || 'fake-api-key';
  }

  private apiUrl(): string {
    if (!parentConfig.apiBaseUrl) {
      throw new ParentAuthError('MOBILE_API_URL_MISSING', authMessages.MOBILE_API_URL_MISSING);
    }
    return parentConfig.apiBaseUrl;
  }

  private toSession(payload: FirebasePayload, previousUser?: ParentUser): Session {
    const subject = payload.localId ?? payload.user_id ?? previousUser?.subject;
    const idToken = payload.idToken ?? payload.id_token;
    const refreshToken = payload.refreshToken ?? payload.refresh_token;
    const expiresIn = Number(payload.expiresIn ?? payload.expires_in ?? '3600');
    if (!subject || !idToken || !refreshToken || !Number.isFinite(expiresIn) || expiresIn <= 0) {
      throw new ParentAuthError('INVALID_AUTH_RESPONSE', 'Thông tin đăng nhập không hợp lệ. Hãy thử lại.');
    }
    const user: ParentUser = { subject, email: payload.email ?? previousUser?.email ?? '', role: 'parent' };
    return { user, idToken, refreshToken, expiresAt: Date.now() + expiresIn * 1000 };
  }

  private async postFirebase(url: string, body: object): Promise<FirebasePayload> {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).catch((error: unknown) => {
      if (__DEV__) {
        const requestUrl = new URL(url);
        console.info('parent_firebase_auth_network_failed', {
          host: requestUrl.host,
          path: requestUrl.pathname,
          errorName: error instanceof Error ? error.name : 'UnknownError',
        });
      }
      throw new ParentAuthError('AUTH_NETWORK_ERROR', 'Không kết nối được dịch vụ xác thực. Hãy thử lại sau.');
    });
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

  private logAuthFailure(stage: string, error: unknown): void {
    if (!__DEV__) return;
    console.warn('parent_auth_stage_failed', {
      stage,
      code: error instanceof ParentApplicationError ? error.code : 'UNEXPECTED_AUTH_ERROR',
      errorName: error instanceof Error ? error.name : 'UnknownError',
    });
  }
}
