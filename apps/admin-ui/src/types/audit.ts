export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actorId: string;
  actorRole: string;
  action: string;
  targetResource: string;
  detailsRedacted: boolean;
  ipHash: string;
}
