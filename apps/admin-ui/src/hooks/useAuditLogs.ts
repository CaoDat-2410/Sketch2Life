import { useState, useEffect } from 'react';
import { auditLogService } from '../services/auditLogService';

export function useAuditLogs() {
  const [logs, setLogs] = useState<any[]>([]);
  useEffect(() => { auditLogService.queryLogs().then(setLogs); }, []);
  return { logs, refresh: () => auditLogService.queryLogs().then(setLogs) };
}
