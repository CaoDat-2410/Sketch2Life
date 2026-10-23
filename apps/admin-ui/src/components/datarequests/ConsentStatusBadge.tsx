import React from 'react';

export const ConsentStatusBadge: React.FC<{ status: 'verified' | 'pending' | 'revoked' }> = ({ status }) => {
  const colors = {
    verified: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    pending: 'bg-amber-50 text-amber-700 border-amber-200',
    revoked: 'bg-rose-50 text-rose-700 border-rose-200',
  };
  return <span className={`px-2 py-0.5 text-xs font-medium border rounded-full ${colors[status]}`}>{status}</span>;
};
