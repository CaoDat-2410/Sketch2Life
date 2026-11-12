import React from 'react';

export const AiComparisonSlider: React.FC<{ originalUrl: string; interpretedUrl: string }> = () => (
  <div className="relative border border-slate-200 rounded-xl overflow-hidden aspect-video bg-white flex items-center justify-center text-xs text-slate-400">
    So sánh Nét vẽ gốc (Child) vs Nét vẽ nhận dạng AI (Vector)
  </div>
);
