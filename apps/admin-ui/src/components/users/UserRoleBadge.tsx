import React from 'react';
import type { AdultRole } from '../../types/admin';

export const UserRoleBadge: React.FC<{ role: AdultRole }> = ({ role }) => {
  const styles: Record<AdultRole, string> = {
    admin: 'bg-purple-50 text-purple-700 border-purple-200',
    guide: 'bg-blue-50 text-blue-700 border-blue-200',
    parent: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  };
  return (
    <span className={`inline-flex px-2 py-0.5 text-xs font-semibold border rounded-full ${styles[role]}`}>
      {role.toUpperCase()}
    </span>
  );
};
