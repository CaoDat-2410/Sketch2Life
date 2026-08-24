export type AuthenticatedUser = Readonly<{
  subject: string;
  displayName?: string;
}>;

/** Provider-neutral boundary; the Firebase adapter is added with the approved auth feature. */
export interface AuthSessionPort {
  currentUser(): Promise<AuthenticatedUser | null>;
  getIdToken(): Promise<string>;
  signOut(): Promise<void>;
}
