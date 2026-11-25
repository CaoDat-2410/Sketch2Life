import type { ParentApiPort } from '../ports/ParentPorts';
import type { ParentLessonListOptions } from '../../domain/types';

export class ParentLessonUseCases {
  constructor(private readonly api: ParentApiPort) {}

  list(options?: ParentLessonListOptions) { return this.api.listLessons(options); }
  get(lessonId: string) { return this.api.getLesson(lessonId); }
  listInvitations() { return this.api.listLessonInvitations(); }
  acceptInvitation(invitationId: string, actionIdentity?: string) { return this.api.acceptLessonInvitation(invitationId, actionIdentity); }
  declineInvitation(invitationId: string, actionIdentity?: string) { return this.api.declineLessonInvitation(invitationId, actionIdentity); }
  listGroupInvitations() { return this.api.listParentGroupInvitations(); }
  acceptGroupInvitation(membershipId: string, actionIdentity?: string) { return this.api.acceptParentGroupInvitation(membershipId, actionIdentity); }
  declineGroupInvitation(membershipId: string, actionIdentity: string) { return this.api.declineParentGroupInvitation(membershipId, actionIdentity); }
  leaveGroup(organizationId: string, parentGroupId: string, membershipId: string, revision: number, actionIdentity: string) {
    return this.api.leaveParentGroup(organizationId, parentGroupId, membershipId, revision, actionIdentity);
  }
  listGroupMemberships(cursor?: string | null) { return this.api.listParentGroupMemberships(cursor); }
}
