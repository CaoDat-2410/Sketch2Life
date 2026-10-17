import React from 'react';

export const ObjectiveTag: React.FC<{ label: string }> = ({ label }) => (
  <span className="inline-block px-2 py-0.5 bg-amber-50 text-amber-700 text-[11px] font-medium rounded border border-amber-200 mr-1.5 mb-1.5">
    {label}
  </span>
);
