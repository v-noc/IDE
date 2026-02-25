import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface Commit {
    id: string;
    author: string;
    initials: string;
    timestamp: string;
    message: string;
}

interface VersioningState {
    isOpen: boolean;
    commits: Commit[];
    selectedCommitId: string | null;
    togglePanel: () => void;
    setOpen: (open: boolean) => void;
    setSelectedCommit: (id: string | null) => void;
}

const DUMMY_COMMITS: Commit[] = [
    {
        id: '1',
        author: 'Emily Alba',
        initials: 'EA',
        timestamp: '06/20/2023 10:30 AM',
        message: 'Updating the laws for Illinois state.',
    },
    {
        id: '2',
        author: 'Emily Alba',
        initials: 'EA',
        timestamp: '06/20/2023 10:30 AM',
        message: 'New version to reflect the changes we discussed in our meeting this morning',
    },
    {
        id: '3',
        author: 'Dave Smith',
        initials: 'DS',
        timestamp: '06/20/2023 10:30 AM',
        message: 'Uploading a new training module. Please review by our next meeting',
    },
    {
        id: '4',
        author: 'Tom Johnson',
        initials: 'TJ',
        timestamp: '06/20/2023 10:30 AM',
        message: 'Adding a new version of our...',
    },
];

export const useVersioningStore = create<VersioningState>()(
    devtools(
        (set) => ({
            isOpen: false,
            commits: DUMMY_COMMITS,
            selectedCommitId: null,
            togglePanel: () => set((state) => ({ isOpen: !state.isOpen })),
            setOpen: (open) => set({ isOpen: open }),
            setSelectedCommit: (id) => set({ selectedCommitId: id }),
        }),
        { name: 'versioning-store' }
    )
);
