import type { AuthenticatedUser, AuthSessionPort } from "./AuthSessionPort";

type FirebaseAuthConfig = Readonly<{ apiKey: string; apiBaseUrl?: string }>;
type FirebaseTokenPayload = Readonly<{
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
}>;
type BackendRegistrationPayload = Readonly<{
  status?: string;
  role?: string;
  code?: string;
}>;
type BackendAccountPayload = Readonly<{ role?: string; state?: string }>;
type StoredSession = Readonly<{
  user: AuthenticatedUser;
  idToken: string;
  refreshToken: string;
  expiresAt: number;
}>;
type FetchPort = typeof fetch;

const IDENTITY_TOOLKIT_URL = "https://identitytoolkit.googleapis.com/v1";
const SECURE_TOKEN_URL = "https://securetoken.googleapis.com/v1/token";

const publicErrorMessages: Record<string, string> = {
  ACCOUNT_SETUP_UNAVAILABLE: "Không thể tạo tài khoản với thông tin này.",
  IDENTITY_PROVIDER_UNAVAILABLE: "Dịch vụ đăng ký đang tạm thời không khả dụng.",
  INVALID_REGISTRATION_REQUEST: "Email hoặc mật khẩu chưa đúng yêu cầu.",
  REGISTRATION_UNAVAILABLE: "Đăng ký hiện không khả dụng.",
  RATE_LIMITED: "Bạn đã thử đăng ký nhiều lần. Hãy thử lại sau.",
  ACCOUNT_ROLE_MISMATCH: "Tài khoản này không thuộc ứng dụng phụ huynh.",
  USER_NOT_FOUND: "Nếu email đã đăng ký, hướng dẫn đặt lại mật khẩu sẽ được gửi.",
  REGISTRATION_NETWORK_ERROR: "Không kết nối được máy chủ đăng ký. Hãy thử lại.",
  API_KEY_INVALID:
    "Cấu hình Firebase Auth chưa hợp lệ. Vui lòng báo quản trị viên kiểm tra.",
  "API key not valid. Please pass a valid API key.":
    "Cấu hình Firebase Auth chưa hợp lệ. Vui lòng báo quản trị viên kiểm tra.",
  EMAIL_EXISTS: "Email này đã được đăng ký.",
  INVALID_EMAIL: "Email không hợp lệ.",
  INVALID_LOGIN_CREDENTIALS: "Email hoặc mật khẩu không đúng.",
  EMAIL_NOT_FOUND: "Email hoặc mật khẩu không đúng.",
  INVALID_PASSWORD: "Email hoặc mật khẩu không đúng.",
  WEAK_PASSWORD: "Mật khẩu cần có ít nhất 6 ký tự.",
  TOO_MANY_ATTEMPTS_TRY_LATER: "Thử lại sau ít phút.",
};

export class FirebaseAuthRequestError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "FirebaseAuthRequestError";
    this.code = code;
  }
}

/** Firebase Authentication REST adapter; tokens stay in memory for this app process. */
export class FirebaseAuthSession implements AuthSessionPort {
  private session: StoredSession | null = null;
  private refreshInFlight: Promise<string> | null = null;

  constructor(
    private readonly config: FirebaseAuthConfig,
    private readonly fetcher: FetchPort = fetch,
    private readonly now: () => number = Date.now,
  ) {}

  async currentUser(): Promise<AuthenticatedUser | null> {
    return this.session?.user ?? null;
  }

  async signIn(email: string, password: string): Promise<AuthenticatedUser> {
    const user = await this.authenticate(email, password);
    try {
      await this.requireParentRole();
      return user;
    } catch (error) {
      await this.signOut();
      throw error;
    }
  }

  async signUp(email: string, password: string): Promise<AuthenticatedUser> {
    const normalizedEmail = email.trim();
    await this.registerWithBackend(normalizedEmail, password);
    const user = await this.authenticate(normalizedEmail, password);
    try {
      await this.requireParentRole();
      return user;
    } catch (error) {
      await this.signOut();
      throw error;
    }
  }

  async resetPassword(email: string): Promise<void> {
    try {
      await this.postJson(
        `${IDENTITY_TOOLKIT_URL}/accounts:sendOobCode?key=${encodeURIComponent(this.apiKey())}`,
        { requestType: "PASSWORD_RESET", email: email.trim() },
      );
    } catch (error) {
      if (
        error instanceof FirebaseAuthRequestError &&
        (error.code === "EMAIL_NOT_FOUND" || error.code === "USER_NOT_FOUND")
      ) {
        return;
      }
      throw error;
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    const existing = this.session;
    if (!existing) throw new Error("Đăng nhập để tiếp tục.");
    const reauthenticated = await this.postJson(
      `${IDENTITY_TOOLKIT_URL}/accounts:signInWithPassword?key=${encodeURIComponent(this.apiKey())}`,
      {
        email: existing.user.email ?? "",
        password: currentPassword,
        returnSecureToken: true,
      },
    );
    const confirmed = this.toSession(reauthenticated, existing.user);
    if (confirmed.user.subject !== existing.user.subject) {
      throw new FirebaseAuthRequestError(
        "ACCOUNT_REAUTHENTICATION_FAILED",
        "Không thể xác nhận lại tài khoản hiện tại.",
      );
    }
    const updated = await this.postJson(
      `${IDENTITY_TOOLKIT_URL}/accounts:update?key=${encodeURIComponent(this.apiKey())}`,
      { idToken: confirmed.idToken, password: newPassword, returnSecureToken: true },
    );
    this.session = this.toSession(updated, existing.user);
  }

  async getIdToken(): Promise<string> {
    if (!this.session) {
      throw new Error("Đăng nhập để tiếp tục.");
    }
    if (this.session.expiresAt > this.now() + 60_000) {
      return this.session.idToken;
    }
    return this.refreshIdToken();
  }

  async signOut(): Promise<void> {
    this.session = null;
    this.refreshInFlight = null;
  }

  private async authenticate(
    email: string,
    password: string,
  ): Promise<AuthenticatedUser> {
    const payload = await this.postJson(
      `${IDENTITY_TOOLKIT_URL}/accounts:signInWithPassword?key=${encodeURIComponent(this.apiKey())}`,
      { email: email.trim(), password, returnSecureToken: true },
    );
    const session = this.toSession(payload);
    this.session = session;
    return session.user;
  }

  private async registerWithBackend(email: string, password: string): Promise<void> {
    const baseUrl = this.config.apiBaseUrl?.trim().replace(/\/+$/, "");
    if (!baseUrl) {
      throw new FirebaseAuthRequestError(
        "REGISTRATION_NETWORK_ERROR",
        publicErrorMessages.REGISTRATION_NETWORK_ERROR,
      );
    }

    let response: Response;
    try {
      response = await this.fetcher(`${baseUrl}/api/auth/v1/registrations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
    } catch {
      throw new FirebaseAuthRequestError(
        "REGISTRATION_NETWORK_ERROR",
        publicErrorMessages.REGISTRATION_NETWORK_ERROR,
      );
    }

    let payload: BackendRegistrationPayload;
    try {
      payload = (await response.json()) as BackendRegistrationPayload;
    } catch {
      throw new FirebaseAuthRequestError(
        "REGISTRATION_NETWORK_ERROR",
        publicErrorMessages.REGISTRATION_NETWORK_ERROR,
      );
    }
    if (!response.ok) {
      const code = typeof payload.code === "string" ? payload.code : "REGISTRATION_NETWORK_ERROR";
      throw new FirebaseAuthRequestError(
        code,
        publicErrorMessages[code] ?? "Không thể tạo tài khoản lúc này. Vui lòng thử lại.",
      );
    }
    if (payload.status !== "IDENTITY_CREATED" || payload.role !== "parent") {
      throw new FirebaseAuthRequestError(
        "REGISTRATION_NETWORK_ERROR",
        publicErrorMessages.REGISTRATION_NETWORK_ERROR,
      );
    }
  }

  private async requireParentRole(): Promise<void> {
    const baseUrl = this.config.apiBaseUrl?.trim().replace(/\/+$/, "");
    if (!baseUrl) {
      throw new FirebaseAuthRequestError(
        "REGISTRATION_NETWORK_ERROR",
        publicErrorMessages.REGISTRATION_NETWORK_ERROR,
      );
    }
    const idToken = await this.getIdToken();
    let response: Response;
    try {
      response = await this.fetcher(`${baseUrl}/api/auth/v1/me`, {
        headers: { Authorization: `Bearer ${idToken}`, Accept: "application/json" },
      });
    } catch {
      throw new FirebaseAuthRequestError(
        "REGISTRATION_NETWORK_ERROR",
        publicErrorMessages.REGISTRATION_NETWORK_ERROR,
      );
    }
    const payload = (await response.json().catch(() => ({}))) as BackendAccountPayload;
    if (!response.ok || payload.role !== "parent" || payload.state !== "active") {
      throw new FirebaseAuthRequestError(
        "ACCOUNT_ROLE_MISMATCH",
        publicErrorMessages.ACCOUNT_ROLE_MISMATCH,
      );
    }
  }

  private async refreshIdToken(): Promise<string> {
    if (this.refreshInFlight) return this.refreshInFlight;
    const existing = this.session;
    if (!existing) throw new Error("Đăng nhập để tiếp tục.");

    this.refreshInFlight = (async () => {
      const payload = await this.postForm(
        `${SECURE_TOKEN_URL}?key=${encodeURIComponent(this.apiKey())}`,
        `grant_type=refresh_token&refresh_token=${encodeURIComponent(existing.refreshToken)}`,
      );
      const refreshed = this.toSession(payload, existing.user);
      this.session = refreshed;
      return refreshed.idToken;
    })();

    try {
      return await this.refreshInFlight;
    } finally {
      this.refreshInFlight = null;
    }
  }

  private apiKey(): string {
    const apiKey = this.config.apiKey.trim();
    if (!apiKey)
      throw new Error("Thiếu cấu hình Firebase trong file .env ở thư mục gốc.");
    return apiKey;
  }

  private toSession(
    payload: FirebaseTokenPayload,
    previousUser?: AuthenticatedUser,
  ): StoredSession {
    const subject = payload.localId ?? payload.user_id ?? previousUser?.subject;
    const idToken = payload.idToken ?? payload.id_token;
    const refreshToken = payload.refreshToken ?? payload.refresh_token;
    const expiresIn = Number(payload.expiresIn ?? payload.expires_in ?? "3600");
    if (
      !subject ||
      !idToken ||
      !refreshToken ||
      !Number.isFinite(expiresIn) ||
      expiresIn <= 0
    ) {
      throw new Error("Firebase trả về dữ liệu phiên đăng nhập không hợp lệ.");
    }
    return {
      user: {
        subject,
        email: payload.email ?? previousUser?.email,
        displayName: previousUser?.displayName,
        role: "parent",
      },
      idToken,
      refreshToken,
      expiresAt: this.now() + expiresIn * 1000,
    };
  }

  private async postJson(
    url: string,
    body: object,
  ): Promise<FirebaseTokenPayload> {
    return this.readResponse(
      await this.fetcher(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    );
  }

  private async postForm(
    url: string,
    body: string,
  ): Promise<FirebaseTokenPayload> {
    return this.readResponse(
      await this.fetcher(url, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      }),
    );
  }

  private async readResponse(
    response: Response,
  ): Promise<FirebaseTokenPayload> {
    const payload = (await response.json()) as FirebaseTokenPayload;
    if (!response.ok) {
      const code = payload.error?.message ?? "FIREBASE_AUTH_ERROR";
      throw new FirebaseAuthRequestError(
        code,
        publicErrorMessages[code] ??
          "Không thể xác thực lúc này. Vui lòng thử lại.",
      );
    }
    return payload;
  }
}
