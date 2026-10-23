import React from 'react';

export interface RejectAiSuggestionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const RejectAiSuggestionModal: React.FC<RejectAiSuggestionModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl p-6 max-w-sm w-full shadow-xl">
        <h3 className="font-bold text-sm text-slate-900 mb-2">RejectAiSuggestionModal</h3>
        <button onClick={onClose} className="mt-4 px-3 py-1.5 bg-slate-100 rounded text-xs">Đóng</button>
      </div>
    </div>
  );
};
