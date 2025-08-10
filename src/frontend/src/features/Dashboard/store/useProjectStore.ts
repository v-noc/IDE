import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type { NodeType, ProjectTreeResponse } from "@/features/Dashboard/service/useProject";

const uuidv4 = () => new Date().getTime().toString() + Math.random().toString(36).substr(2, 9);

interface ProjectState {
    selectedNodeId: string | null;
    setSelectedNodeId: (nodeId: string | null) => void;
    activeNodeId: string | null;
    expandedNodeIds: string[];
    toggleNodeExpansion: (nodeId: string) => void;
    virtualFolderStructures: ProjectTreeResponse[];
    addVirtualNode: (parentId: string, name: string, type: NodeType) => void;
    projectData: ProjectTreeResponse | null;
    setProjectData: (data: ProjectTreeResponse) => void;
}

const addNodeToParent = (nodes: ProjectTreeResponse[], parentId: string, newNode: ProjectTreeResponse): ProjectTreeResponse[] => {
    return nodes.map(node => {
        if (node.key === parentId) {
            return {
                ...node,
                children: [...(node.children || []), newNode],
            };
        }
        if (node.children) {
            return {
                ...node,
                children: addNodeToParent(node.children, parentId, newNode),
            };
        }
        return node;
    });
};

const useProjectStore = create<ProjectState>()(
    devtools(
        immer((set) => ({
            selectedNodeId: null,
            setSelectedNodeId: (nodeId) => set({ selectedNodeId: nodeId }),
            activeNodeId: null,
            expandedNodeIds: [],
            toggleNodeExpansion: (nodeId) => {
                set((state) => {
                    const index = state.expandedNodeIds.indexOf(nodeId);
                    if (index > -1) {
                        state.expandedNodeIds.splice(index, 1);
                    } else {
                        state.expandedNodeIds.push(nodeId);
                    }
                });
            },
            projectData: null,
            setProjectData: (data) => set({ projectData: data }),
            virtualFolderStructures: [],
            addVirtualNode: (parentId, name, type) => {
                const newNode: ProjectTreeResponse = {
                    key: uuidv4(),
                    name,
                    path: "",
                    node_type: type,
                    label: name,
                    children: type === "folder" ? [] : [],
                    isVirtual: true,
                    parentId,
                };
                set(state => {
                    state.virtualFolderStructures = addNodeToParent(state.virtualFolderStructures, parentId, newNode);
                })
            },
        }))
    )
);

export default useProjectStore; 