import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";
import { findNodeByKey } from "@/features/Dashboard/utils/findNode";
// const uuidv4 = () => new Date().getTime().toString() + Math.random().toString(36).substr(2, 9);

interface ProjectState {
    selectedNode: AnyNodeTree | null;
    setSelectedNode: (node: AnyNodeTree) => void;
    secondarySelectedNode: AnyNodeTree | null;
    setSecondarySelectedNode: (node: AnyNodeTree | null) => void;
    focusedNode: AnyNodeTree | null; // deprecated in favor of focusStack[focusStack.length-1]
    setFocusedNode: (node: AnyNodeTree | null) => void; // keeps compatibility
    focusStack: AnyNodeTree[];
    pushFocus: (node: AnyNodeTree) => void;
    popFocus: () => void;
    clearFocus: () => void;
    activeNodeId: string | null;
    expandedNodeIds: string[];
    toggleNodeExpansion: (nodeId: string) => void;
    // virtualFolderStructures: AnyNodeTree[];
    // addVirtualNode: (parentId: string, name: string, type: NodeType) => void;
    projectData: ProjectNodeTree | null;
    setProjectData: (data: ProjectNodeTree) => void;
}

// const addNodeToParent = (nodes: AnyNodeTree[], parentId: string, newNode: AnyNodeTree): AnyNodeTree[] => {
//     return nodes.map(node => {
//         if (node.key === parentId) {
//             return {
//                 ...node,
//                 children: [...(node.children || []), newNode],
//             };
//         }
//         if (node.children) {
//             return {
//                 ...node,
//                 children: addNodeToParent(node.children as AnyNodeTree[], parentId, newNode),
//             };
//         }
//         return node;
//     });
// };

const useProjectStore = create<ProjectState>()(
    devtools(
        immer((set) => ({
            selectedNode: null,
            setSelectedNode: (node) => set({ selectedNode: node }),
            secondarySelectedNode: null,
            setSecondarySelectedNode: (node) => set({ secondarySelectedNode: node }),
            focusedNode: null,
            setFocusedNode: (node) => set({ focusedNode: node }),
            focusStack: [],
            pushFocus: (node) => set((state) => {
                state.focusStack.push(node);
                state.focusedNode = node;
            }),
            popFocus: () => set((state) => {
                state.focusStack.pop();
                state.focusedNode = state.focusStack[state.focusStack.length - 1] ?? null;
            }),
            clearFocus: () => set({ focusStack: [], focusedNode: null }),
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
            setProjectData: (data) => set((state) => {
                state.projectData = data;
                // Remap focus stack nodes to the new project tree by _key
                if (state.focusStack.length > 0 && data) {
                    const remapped = state.focusStack
                        .map((n) => findNodeByKey(data, n._key))
                        .filter((n): n is AnyNodeTree => n != null);
                    state.focusStack = remapped;
                    state.focusedNode = remapped.length > 0 ? remapped[remapped.length - 1] : null;
                } else if (!data) {
                    // If project data is cleared, also clear focus
                    state.focusStack = [];
                    state.focusedNode = null;
                }
            }),
            // virtualFolderStructures: []
            // addVirtualNode: (parentId, name, type) => {
            //     const newNode: AnyNodeTree & { parentId?: string } = {
            //         id: uuidv4(),
            //         key: uuidv4(),
            //         created_at: new Date().toISOString(),
            //         updated_at: new Date().toISOString(),
            //         name,
            //         description: "",
            //         node_type: type,
            //         children: type === "folder" ? [] : [],
            //         parentId,
            //     };
            //     set(state => {
            //         state.virtualFolderStructures = addNodeToParent(state.virtualFolderStructures, parentId, newNode);
            //     })
            // },
        }))
    )
);

export default useProjectStore; 