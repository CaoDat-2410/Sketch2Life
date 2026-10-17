import React from 'react';
import type { AuditLogEntry } from '../../types/audit';

export const AuditLogTable: React.FC<{ entries?: AuditLogEntry[] }> = ({ entries = [] }) => (
  <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden p-4 text-xs">
    Bảng nhật ký kiểm toán hệ thống (Audit Trail).
  </div>
);
