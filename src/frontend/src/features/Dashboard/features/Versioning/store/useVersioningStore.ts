import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface Commit {
    id: string;
    author: string;
    initials: string;
    timestamp: string;
    message: string;
}

export type DiffStatus = 'added' | 'removed' | 'updated' | null;

interface VersioningState {
    isOpen: boolean;
    commits: Commit[];
    selectedCommitId: string | null;
    nodeDiffs: Record<string, DiffStatus>;
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

const MOCK_DIFFS: Record<string, Record<string, DiffStatus>> = {
    '1': {
        'FunctionSchema/f6c92d63-9951-4ddd-953e-755dfdc174f2': 'added',
        'FileSchema/cb66b194-9ab0-4d9c-a126-66477c033786': 'updated',
        'FunctionSchema/fe252706-863d-4187-b2f4-cc403ee9fb28': 'removed',
    },
    '2': {
        'FolderSchema/3d22733e-1c90-456b-ba1e-23b25e3773f1': 'added',
        'FolderSchema/3d22733e-1c90-456b-ba1e-23b25e3773f1': 'updated',
    },
    '3': {
        'node-1': 'updated',
        'node-6': 'added',
    },
    '4': {
        'node-2': 'removed',
        'node-7': 'added',
    }
};

export const useVersioningStore = create<VersioningState>()(
    devtools(
        (set) => ({
            isOpen: false,
            commits: DUMMY_COMMITS,
            selectedCommitId: null,
            nodeDiffs: {},
            togglePanel: () => set((state) => ({ isOpen: !state.isOpen })),
            setOpen: (open) => set({ isOpen: open }),
            setSelectedCommit: (id) => set({
                selectedCommitId: id,
                nodeDiffs: id ? (MOCK_DIFFS[id] ?? {}) : {}
            }),
        }),
        { name: 'versioning-store' }
    )
);
