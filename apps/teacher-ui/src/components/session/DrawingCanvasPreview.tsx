import React from 'react';

export const DrawingCanvasPreview: React.FC<{ imageUrl?: string; childName?: string }> = ({ imageUrl, childName }) => (
  <div className="bg-slate-50 border border-slate-200 rounded-xl overflow-hidden aspect-video flex items-center justify-center">
    {imageUrl ? <img src={imageUrl} alt={childName} className="object-contain w-full h-full" /> : <span className="text-xs text-slate-400">Chưa có ảnh nét vẽ</span>}
  </div>
);
