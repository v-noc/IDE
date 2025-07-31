import { create } from 'zustand';
import type { ProjectNode } from '@/types/project';

interface ProjectState {
    selectedNode: ProjectNode | null;
    setSelectedNode: (node: ProjectNode | null) => void;
    activeNodeId: string | null;
    expandedNodeIds: Set<string>;
    toggleNodeExpansion: (nodeId: string) => void;
}

const useProjectStore = create<ProjectState>((set, get) => ({
    selectedNode: null,
    setSelectedNode: (node) => set({ selectedNode: node }),
    activeNodeId: null,
    expandedNodeIds: new Set<string>(),
    toggleNodeExpansion: (nodeId) => {
        const { expandedNodeIds } = get();
        const newExpandedNodeIds = new Set(expandedNodeIds);
        if (newExpandedNodeIds.has(nodeId)) {
            newExpandedNodeIds.delete(nodeId);
        } else {
            newExpandedNodeIds.add(nodeId);
        }
        set({ expandedNodeIds: newExpandedNodeIds });
    },
}));

export default useProjectStore; 