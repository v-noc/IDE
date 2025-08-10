import { useCallback, useMemo } from "react";
import { addEdge, type Edge, type Connection, type OnConnect } from "@xyflow/react";
import type { VirtualFolderResponse, ProjectTreeResponse, FieldResponse, NodeType } from "@/features/Dashboard/service/useProject";
import { useGetVirtualFolders, useGetProjectTreeWithKeyProject } from "@/features/Dashboard/service/useProject";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";


interface CommonVNode {
    key: string;
    name: string;
    node_type: string; // final renderer type: function | class | virtual_folder | etc.
    qname?: string;
    icon?: string;
    theme?: unknown;
    call_order?: number | null;
    inputs?: FieldResponse[];
    outputs?: FieldResponse[];
    fields?: FieldResponse[];
    methods?: { name: string; returnType?: string }[];
    children: CommonVNode[];
}



// -------- Unifiers (return full data for class/function) --------
function unifyProjectTree(node: ProjectTreeResponse): CommonVNode {
    const methodChildren = (node.children || []).filter((c) => c.node_type === "function");
    const nonMethodChildren = (node.children || []).filter((c) => c.node_type !== "function");
    return {
        key: node.key,
        name: node.name,
        node_type: node.node_type,
        qname: node.path || node.key,
        inputs: node.inputs,
        outputs: node.outputs,
        fields: node.fields,
        methods: methodChildren.map((m) => ({ name: m.name })),
        children: nonMethodChildren.map(unifyProjectTree),
    } as CommonVNode;
}

function unifyVirtualFolder(vf: VirtualFolderResponse): CommonVNode {
    const lt = vf.link_to;
    const base: CommonVNode = {
        key: vf.key, // always use virtual folder key (do not use link_to id)
        name: vf.name || lt?.name || "",
        node_type: (lt?.node_type || vf.node_type) as NodeType,
        qname: vf.qname || lt?.qname,
        children: (vf.children || []).map(unifyVirtualFolder),
    };
    if (lt?.node_type === "class") {
        const methodChildren = base.children.filter((c) => c.node_type === "function");
        const nonMethodChildren = base.children.filter((c) => c.node_type !== "function");
        return { ...base, methods: methodChildren, children: nonMethodChildren, fields: lt?.fields, };
    } else if (lt?.node_type == "function") {
        return {
            ...base, inputs: lt?.inputs,
            outputs: lt?.outputs,
        }
    }
    return base;
}

function findNodeAndParentByKey(
    root: CommonVNode,
    id: string
): { node: CommonVNode | null; parent: CommonVNode | null } {
    if (root.key === id) return { node: root, parent: null };
    let found: CommonVNode | null = null;
    let parent: CommonVNode | null = null;
    const walk = (n: CommonVNode) => {
        for (const c of n.children || []) {
            if ((c.key === id) && (c.node_type === "class" || c.node_type === "function")) {
                found = c;
                parent = n;
                return;
            }
            walk(c);
            if (found) return;
        }
    };
    walk(root);
    return { node: found, parent };
}



// Accept: none (auto-fetch), a single VF, an array of VFs, or a project tree
export function useCanvasGraph(
    projectId?: string,

) {
    const { projectData } = useProjectStore();
    const projectKey = projectId || projectData?.key || "";
    const selectedNodeId = useProjectStore((s) => s.selectedNodeId);
    // keep selected for upcoming steps; expanded will be used later when rendering
    // const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);

    // Fetch if source not provided
    const { data: vfs } = useGetVirtualFolders(projectKey);
    const { data: projTree } = useGetProjectTreeWithKeyProject({ key: projectKey });
    // Step 1: extract selected node and its parent from project tree or virtual folders
    const selectedFromSources = useMemo(() => {
        if (!selectedNodeId) return { node: null as CommonVNode | null, parent: null as CommonVNode | null };
        // Prefer project tree first
        if (projTree) {

            const hit = findNodeAndParentByKey(projTree, selectedNodeId);
            if (hit.node) return hit;
        }
        if (vfs && vfs.length > 0) {
            for (const vf of vfs) {
                const vfRoot = unifyVirtualFolder(vf);
                const hit = findNodeAndParentByKey(vfRoot, selectedNodeId);
                if (hit.node) return hit;
            }
        }
        return { node: null as CommonVNode | null, parent: null as CommonVNode | null };
    }, [selectedNodeId, projTree, vfs]);


    const onNodesChange = useCallback(() => { }, []);
    const onEdgesChange = useCallback(() => { }, []);

    const onConnect = useCallback(
        (setEdges: (updater: Edge[] | ((eds: Edge[]) => Edge[])) => void): OnConnect =>
            (connection: Connection) => setEdges((eds) => addEdge({ ...connection, type: "smartEdge" }, eds)),
        []
    );

    return {
        nodes: [],
        edges: [],
        selected: selectedFromSources.node,
        parent: selectedFromSources.parent,
        onNodesChange,
        onEdgesChange,
        onConnect,
    };
}