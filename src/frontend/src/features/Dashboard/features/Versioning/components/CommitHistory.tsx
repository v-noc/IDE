import React from 'react';
import { useVersioningStore } from '../store/useVersioningStore';
import CommitItem from './CommitItem';

const CommitHistory: React.FC = () => {
    const { commits, selectedCommitId, setSelectedCommit } = useVersioningStore();

    return (
        <div className="flex flex-col px-3 py-4">
            {commits.map((commit, index) => (
                <CommitItem
                    key={commit.id}
                    commit={commit}
                    isLast={index === commits.length - 1}
                    isActive={selectedCommitId === commit.id}
                    onClick={() => setSelectedCommit(commit.id)}
                />
            ))}
        </div>
    );
};

export default CommitHistory;
