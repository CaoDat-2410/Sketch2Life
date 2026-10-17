import React from 'react';

export const ConfirmErasureDialog: React.FC<{ isOpen: boolean; onConfirm: () => void; onCancel: () => void }> = ({ isOpen, onConfirm, onCancel }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl p-6 max-w-sm w-full">
        <h4 className="font-bold text-sm text-rose-600 mb-2">Xác nhận xóa vĩnh viễn dữ liệu</h4>
        <div className="flex gap-2 justify-end mt-4">
          <button onClick={onCancel} className="px-3 py-1.5 text-xs bg-slate-100 rounded">Hủy</button>
          <button onClick={onConfirm} className="px-3 py-1.5 text-xs bg-rose-600 text-white rounded">Xóa ngay</button>
        </div>
      </div>
    </div>
  );
};
