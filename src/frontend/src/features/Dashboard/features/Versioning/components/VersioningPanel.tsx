import React from 'react';
import { X } from 'lucide-react';
import { useVersioningStore } from '../store/useVersioningStore';
import CommitHistory from './CommitHistory';

const VersioningPanel: React.FC = () => {
    const { togglePanel } = useVersioningStore();

    return (
        <div className="flex h-full w-full flex-col border-l bg-white shadow-sm transition-all duration-300">
            <div className="flex items-center justify-between border-b px-4 py-3">
                <h2 className="text-lg font-semibold text-slate-800">Research</h2>
                <button
                    onClick={togglePanel}
                    className="rounded-md p-1 hover:bg-slate-100 text-slate-500"
                >
                    <X size={20} />
                </button>
            </div>
            <div className="flex-1 overflow-y-auto">
                <CommitHistory />
            </div>
        </div>
    );
};

export default VersioningPanel;
