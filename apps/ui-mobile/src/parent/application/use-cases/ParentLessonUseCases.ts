import type { ParentApiPort } from '../ports/ParentPorts';

export class ParentLessonUseCases {
  constructor(private readonly api: ParentApiPort) {}

  list() { return this.api.listLessons(); }
  get(lessonId: string) { return this.api.getLesson(lessonId); }
  listInvitations() { return this.api.listLessonInvitations(); }
  acceptInvitation(invitationId: string) { return this.api.acceptLessonInvitation(invitationId); }
  declineInvitation(invitationId: string) { return this.api.declineLessonInvitation(invitationId); }
  listGroupInvitations() { return this.api.listParentGroupInvitations(); }
  acceptGroupInvitation(membershipId: string) { return this.api.acceptParentGroupInvitation(membershipId); }
}
