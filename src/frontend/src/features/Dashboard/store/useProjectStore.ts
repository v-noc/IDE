import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";
// const uuidv4 = () => new Date().getTime().toString() + Math.random().toString(36).substr(2, 9);

interface ProjectState {
    selectedNode: AnyNodeTree | null;
    setSelectedNode: (node: AnyNodeTree) => void;
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