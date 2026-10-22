import React from 'react';

export const SessionTimer: React.FC<{ elapsedSeconds: number; maxMinutes?: number }> = ({ elapsedSeconds, maxMinutes = 10 }) => {
  const mins = Math.floor(elapsedSeconds / 60);
  const secs = elapsedSeconds % 60;
  return (
    <div className="px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-mono font-bold flex items-center gap-2">
      <span>⏱</span>
      <span>{mins.toString().padStart(2, '0')}:{secs.toString().padStart(2, '0')}</span>
      <span className="text-slate-400 font-normal">/ {maxMinutes}m</span>
    </div>
  );
};
