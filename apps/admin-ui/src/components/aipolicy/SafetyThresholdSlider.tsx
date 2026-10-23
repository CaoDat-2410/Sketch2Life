import React from 'react';

export const SafetyThresholdSlider: React.FC<{ label: string; value: number }> = ({ label, value }) => (
  <div className="mb-4">
    <div className="flex justify-between text-xs font-medium mb-1">
      <span>{label}</span>
      <span>{value}%</span>
    </div>
    <input type="range" min="0" max="100" defaultValue={value} className="w-full accent-blue-600" />
  </div>
);
