import {
  FirebaseAuthRequestError,
  FirebaseAuthSession,
} from "../src/infrastructure/auth/firebaseAuthSession";

function response(payload: object, ok = true): Response {
  return { ok, json: async () => payload } as Response;
}

describe("FirebaseAuthSession", () => {
  it("creates the account through the backend, then establishes a Firebase session", async () => {
    const fetcher = jest
      .fn()
      .mockResolvedValueOnce(
        response({ status: "IDENTITY_CREATED", email_verified: false }),
      )
      .mockResolvedValueOnce(
        response({
        localId: "synthetic-user-1",
        email: "adult@example.test",
        idToken: "synthetic-id-token",
        refreshToken: "synthetic-refresh-token",
        expiresIn: "3600",
        }),
      );
    const session = new FirebaseAuthSession(
      {
        apiKey: "public-api-key",
        apiBaseUrl: "http://10.0.2.2:8000/",
      },
      fetcher,
    );

    const user = await session.signUp("adult@example.test", "local-password");

    expect(user).toEqual({
      subject: "synthetic-user-1",
      displayName: "adult@example.test",
    });
    expect(fetcher).toHaveBeenNthCalledWith(
      1,
      "http://10.0.2.2:8000/api/auth/v1/registrations",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          email: "adult@example.test",
          password: "local-password",
        }),
      }),
    );
    expect(fetcher).toHaveBeenNthCalledWith(
      2,
      "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=public-api-key",
      expect.objectContaining({ method: "POST" }),
    );
    expect(await session.getIdToken()).toBe("synthetic-id-token");
  });

  it("does not call Firebase sign-in when backend registration fails", async () => {
    const fetcher = jest.fn().mockResolvedValue(
      response({ code: "ACCOUNT_SETUP_UNAVAILABLE" }, false),
    );
    const session = new FirebaseAuthSession(
      { apiKey: "public-api-key", apiBaseUrl: "http://localhost:8000" },
      fetcher,
    );

    await expect(
      session.signUp("adult@example.test", "local-password"),
    ).rejects.toEqual(
      expect.objectContaining<Partial<FirebaseAuthRequestError>>({
        code: "ACCOUNT_SETUP_UNAVAILABLE",
        message: "Không thể tạo tài khoản với thông tin này.",
      }),
    );
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("refreshes an expired ID token using the in-memory refresh token", async () => {
    let now = 1_000_000;
    const fetcher = jest
      .fn()
      .mockResolvedValueOnce(
        response({
          localId: "synthetic-user-1",
          idToken: "expired-id-token",
          refreshToken: "synthetic-refresh-token",
          expiresIn: "1",
        }),
      )
      .mockResolvedValueOnce(
        response({
          user_id: "synthetic-user-1",
          id_token: "fresh-id-token",
          refresh_token: "rotated-refresh-token",
          expires_in: "3600",
        }),
      );
    const session = new FirebaseAuthSession(
      { apiKey: "public-api-key" },
      fetcher,
      () => now,
    );
    await session.signIn("adult@example.test", "local-password");
    now += 2_000;

    await expect(session.getIdToken()).resolves.toBe("fresh-id-token");
    expect(fetcher).toHaveBeenLastCalledWith(
      "https://securetoken.googleapis.com/v1/token?key=public-api-key",
      expect.objectContaining({
        method: "POST",
        body: "grant_type=refresh_token&refresh_token=synthetic-refresh-token",
      }),
    );
  });

  it("clears local tokens on sign-out", async () => {
    const fetcher = jest.fn().mockResolvedValue(
      response({
        localId: "synthetic-user-1",
        idToken: "synthetic-id-token",
        refreshToken: "synthetic-refresh-token",
        expiresIn: "3600",
      }),
    );
    const session = new FirebaseAuthSession(
      { apiKey: "public-api-key" },
      fetcher,
    );
    await session.signIn("adult@example.test", "local-password");

    await session.signOut();

    await expect(session.currentUser()).resolves.toBeNull();
    await expect(session.getIdToken()).rejects.toThrow(
      "Đăng nhập để tiếp tục.",
    );
  });

  it("maps Firebase credential errors to Vietnamese without exposing provider payloads", async () => {
    const fetcher = jest
      .fn()
      .mockResolvedValue(
        response({ error: { message: "INVALID_LOGIN_CREDENTIALS" } }, false),
      );
    const session = new FirebaseAuthSession(
      { apiKey: "public-api-key" },
      fetcher,
    );

    await expect(
      session.signIn("adult@example.test", "bad-password"),
    ).rejects.toEqual(
      expect.objectContaining<Partial<FirebaseAuthRequestError>>({
        code: "INVALID_LOGIN_CREDENTIALS",
        message: "Email hoặc mật khẩu không đúng.",
      }),
    );
  });

  it("shows a safe configuration message when Firebase rejects the Web API key", async () => {
    const fetcher = jest.fn().mockResolvedValue(
      response(
        { error: { message: "API key not valid. Please pass a valid API key." } },
        false,
      ),
    );
    const session = new FirebaseAuthSession(
      { apiKey: "public-api-key" },
      fetcher,
    );

    await expect(
      session.signIn("adult@example.test", "local-password"),
    ).rejects.toEqual(
      expect.objectContaining<Partial<FirebaseAuthRequestError>>({
        message: "Cấu hình Firebase Auth chưa hợp lệ. Vui lòng báo quản trị viên kiểm tra.",
      }),
    );
  });
});
