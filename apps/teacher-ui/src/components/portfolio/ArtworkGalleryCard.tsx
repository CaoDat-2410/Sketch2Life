import React from 'react';

export const ArtworkGalleryCard: React.FC<{ title: string; author: string; date: string }> = ({ title, author, date }) => (
  <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
    <div className="aspect-square bg-slate-50 flex items-center justify-center text-xs text-slate-400">Hình ảnh tranh</div>
    <div className="p-3">
      <h5 className="font-semibold text-xs text-slate-900">{title}</h5>
      <p className="text-[11px] text-slate-500">{author} • {date}</p>
    </div>
  </div>
);
