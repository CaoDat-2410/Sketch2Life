import React from 'react';

export const CreateClassModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl p-6 max-w-sm w-full">
        <h3 className="font-bold text-sm text-slate-900 mb-4">Tạo lớp học mới</h3>
        <button onClick={onClose} className="px-3 py-1.5 bg-slate-100 text-xs rounded-lg">Hủy</button>
      </div>
    </div>
  );
};
