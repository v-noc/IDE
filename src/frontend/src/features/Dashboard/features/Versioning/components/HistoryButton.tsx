import React from 'react';
import { Clock } from 'lucide-react';
import { useVersioningStore } from '../store/useVersioningStore';
import { Button } from '@/components/ui/button';

const HistoryButton: React.FC = () => {
    const { togglePanel, isOpen } = useVersioningStore();

    return (
        <Button
            variant="ghost"
            size="sm"
            onClick={togglePanel}
            className={`flex items-center gap-2 px-3 py-1 h-8 text-xs font-medium rounded-md transition-colors ${isOpen
                    ? 'bg-primary/10 text-primary hover:bg-primary/20'
                    : 'text-muted-foreground hover:bg-muted-foreground/10 hover:text-foreground'
                }`}
        >
            <Clock size={16} />
            <span>History</span>
        </Button>
    );
};

export default HistoryButton;
