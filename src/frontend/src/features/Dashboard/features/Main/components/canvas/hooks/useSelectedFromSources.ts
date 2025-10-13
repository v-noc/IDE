import { useMemo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useGetProjectTreeWithKeyProject, } from "@/features/Dashboard/service/useProject";
import { processVirtualFolders } from "./utils/virtualFolders";
import { findNodeAndParentByKey } from "./utils/finders";
import type { CommonVNode, SelectedFromSources } from "./utils/types";

export function useSelectedFromSources(projectKey: string): SelectedFromSources {
    const selectedNode = useProjectStore((s) => s.selectedNode);
    // const { data: vfs } = useGetVirtualFolders(projectKey);
    const { data: projTree } = useGetProjectTreeWithKeyProject({ key: projectKey });

    return useMemo(() => {
        if (!selectedNode) return { node: null, parent: null };
        if (projTree) {
            const hit = findNodeAndParentByKey(projTree as unknown as CommonVNode, selectedNode.id);
            if (hit.node) return hit;
        }
        // if (vfs && vfs.length > 0) {
        //     for (const vf of vfs) {
        //         const vfRoot = processVirtualFolders(vf);
        //         const hit = findNodeAndParentByKey(vfRoot, selectedNode.id);
        //         if (hit.node) return hit;
        //     }
        // }
        return { node: null, parent: null };
    }, [selectedNode, projTree]);
}


