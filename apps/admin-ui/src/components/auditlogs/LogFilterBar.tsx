import React from 'react';

export const LogFilterBar: React.FC = () => (
  <div className="flex gap-2 mb-4">
    <input type="text" placeholder="Lọc theo Actor ID / Action..." className="px-3 py-2 text-xs border rounded-lg" />
  </div>
);
