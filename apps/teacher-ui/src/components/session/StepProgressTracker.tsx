import React from 'react';

export const StepProgressTracker: React.FC<{ currentStep: number }> = ({ currentStep }) => (
  <div className="flex items-center gap-1.5 py-3">
    {[1, 2, 3, 4, 5, 6, 7, 8].map(step => (
      <div
        key={step}
        className={`flex-1 h-2 rounded-full ${step <= currentStep ? 'bg-blue-600' : 'bg-slate-200'}`}
      />
    ))}
  </div>
);
