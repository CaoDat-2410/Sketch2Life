import React from 'react';

export const ObservationTagSelector: React.FC<{ selectedTags: string[]; onToggle: (tag: string) => void }> = ({ selectedTags, onToggle }) => {
  const tags = ['Tập trung cao', 'Cầm kéo đúng cách', 'Hợp tác nhóm', 'Kể chuyện tự tin', 'Khám phá tò mò'];
  return (
    <div className="flex flex-wrap gap-1.5">
      {tags.map(t => (
        <button
          key={t}
          onClick={() => onToggle(t)}
          className={`px-2.5 py-1 text-xs rounded-full border ${selectedTags.includes(t) ? 'bg-blue-50 text-blue-700 border-blue-300 font-semibold' : 'bg-white text-slate-600 border-slate-200'}`}
        >
          {t}
        </button>
      ))}
    </div>
  );
};
