import type { ParentIdentityPort } from '../ports/ParentPorts';

export class ParentAccountUseCases {
  constructor(private readonly identity: ParentIdentityPort) {}

  currentUser() { return this.identity.currentUser(); }
  signIn(email: string, password: string) { return this.identity.signIn(email, password); }
  signUp(email: string, password: string) { return this.identity.signUp(email, password); }
  signInWithGoogle(idToken: string) { return this.identity.signInWithGoogle(idToken); }
  resetPassword(email: string) { return this.identity.resetPassword(email); }
  changePassword(currentPassword: string, nextPassword: string) {
    return this.identity.changePassword(currentPassword, nextPassword);
  }
  signOut() { return this.identity.signOut(); }
}
