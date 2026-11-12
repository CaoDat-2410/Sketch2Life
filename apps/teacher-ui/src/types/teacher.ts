export interface StudentProfile {
  id: string;
  name: string;
  ageBand: '3-4' | '5-6' | '6-7';
  avatarUrl?: string;
  notes?: string;
  activeSessionId?: string;
}

export interface ClassroomGroup {
  id: string;
  name: string;
  roomNumber: string;
  guideTeacherId: string;
  students: StudentProfile[];
}
