export type AuthenticatedUser = Readonly<{
  subject: string;
  email?: string;
  displayName?: string;
  role: "parent";
}>;

/** Provider-neutral boundary consumed by the Parent app and backend client. */
export interface AuthSessionPort {
  currentUser(): Promise<AuthenticatedUser | null>;
  signIn(email: string, password: string): Promise<AuthenticatedUser>;
  signUp(email: string, password: string): Promise<AuthenticatedUser>;
  resetPassword(email: string): Promise<void>;
  changePassword(currentPassword: string, newPassword: string): Promise<void>;
  getIdToken(): Promise<string>;
  signOut(): Promise<void>;
}
