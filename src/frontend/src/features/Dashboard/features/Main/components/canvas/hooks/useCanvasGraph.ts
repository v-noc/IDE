import { useCallback, useMemo } from "react";
import { addEdge, type Edge, type Connection, type OnConnect, type Node } from "@xyflow/react";
import type { VirtualFolderResponse, FieldResponse, NodeType } from "@/features/Dashboard/service/useProject";
import { useGetVirtualFolders, useGetProjectTreeWithKeyProject } from "@/features/Dashboard/service/useProject";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { getNodeStyle } from "@/features/Dashboard/utils";
import type { ThemeConfig } from "@/features/Dashboard/store/useThemeStore";


interface CommonVNode {
    id: string;
    name: string;
    description?: string | null;
    node_type: NodeType; // final renderer type: function | class | virtual_folder | etc.
    qname?: string;
    icon?: string;
    theme?: ThemeConfig;
    call_order?: number | null;
    inputs?: FieldResponse[];
    outputs?: FieldResponse[];
    fields?: FieldResponse[];
    methods?: { name: string; returnType?: string, node_type: NodeType, theme?: ThemeConfig }[];
    children: CommonVNode[];
    root_id?: string;

}





function processVirtualFolders(vf: VirtualFolderResponse): CommonVNode {
    const lt = vf.link_to;
    const base: CommonVNode = {
        id: vf.id, // always use virtual folder key (do not use link_to id)
        name: vf.name || lt?.name || "",
        call_order: vf.call_order,
        node_type: (lt?.node_type || vf.node_type) as NodeType,
        root_id: lt?.id || vf.id,
        qname: vf.qname || lt?.qname,
        theme: lt?.theme || vf.theme,
        children: (vf.children || []).map(processVirtualFolders),
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
    if (root.id === id) return { node: root, parent: null };
    let found: CommonVNode | null = null;
    let parent: CommonVNode | null = null;
    const walk = (n: CommonVNode) => {
        for (const c of n.children || []) {
            if ((c.id === id) && (c.node_type === "class" || c.node_type === "function")) {
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
    const projectKey = projectId || projectData?.id || "";
    const selectedNode = useProjectStore((s) => s.selectedNode);

    // Fetch if source not provided
    const { data: vfs } = useGetVirtualFolders(projectKey);
    const { data: projTree } = useGetProjectTreeWithKeyProject({ key: projectKey });
    // Step 1: extract selected node and its parent from project tree or virtual folders
    const selectedFromSources = useMemo(() => {

        if (!selectedNode) return { node: null as CommonVNode | null, parent: null as CommonVNode | null };
        // Prefer project tree first
        if (projTree) {

            const hit = findNodeAndParentByKey(projTree, selectedNode.id);
            if (hit.node) return hit;
        }
        if (vfs && vfs.length > 0) {
            for (const vf of vfs) {
                const vfRoot = processVirtualFolders(vf);
                const hit = findNodeAndParentByKey(vfRoot, selectedNode.id);
                if (hit.node) return hit;
            }
        }
        return { node: null as CommonVNode | null, parent: null as CommonVNode | null };
    }, [selectedNode, projTree, vfs]);

    const initialNodes = useMemo((): Node[] => {
        const { node, parent } = selectedFromSources;

        if (!node) return [];

        let nodesToBeRender: CommonVNode[] | null = null;
        let isDefinitionNode = false;

        if (parent == null || !["class", "function"].includes(parent.node_type)) {

            if (selectedNode?.isExpanded) {

                nodesToBeRender = node.children;
            } else {
                isDefinitionNode = true;
                nodesToBeRender = [node];
            }

        } else if (parent != null &&
            ["class", "function"].includes(parent.node_type)) {
            if (selectedNode?.isExpanded) {
                nodesToBeRender = node.children;
            } else {
                nodesToBeRender = parent.children;
            }
        }

        if (nodesToBeRender == null) return [];
        // Sort by call_order (undefined/null treated as Infinity so they go last)
        const ordered = [...nodesToBeRender].sort((a, b) => {
            const ao = a.call_order ?? Number.POSITIVE_INFINITY;
            const bo = b.call_order ?? Number.POSITIVE_INFINITY;
            return ao - bo;
        });

        const nodes: Node[] = [];

        // Add START circle node
        if (!isDefinitionNode) {
            nodes.push({
                type: "circle",
                id: `__start__-${node.id}`,
                position: { x: -160, y: 0 },
                data: { label: "Start", kind: "start" },
            } as unknown as Node);
        }
        ordered.forEach((child, index) => {
            const position = { x: index * 420, y: 0 };
            const isExpandable = child.children.length > 0 || (child.methods && child.methods.length > 0);

            const nodeTheme = getNodeStyle(child);
            if (child.node_type === "class") {

                const derivedMethods = (child.methods && child.methods.length > 0)
                    ? child.methods
                    : child.children
                        .filter((c) => c.node_type === "function")

                nodes.push({
                    type: "class",
                    id: child.id,
                    position,
                    data: {
                        id: child.id,
                        name: child.name,
                        qname: child.qname || "",
                        fields: child.fields,
                        methods: derivedMethods.map((m) => ({ ...m, theme: getNodeStyle(m) })),
                        sourceFile: child.qname || "",
                        icon: child.icon,
                        theme: nodeTheme,
                        isExpandable: isExpandable,
                        isSelected: selectedNode?.id === child.id,
                    },
                });
            } else if (child.node_type === "function" && parent != null && parent.node_type === "class") {

                nodes.push({
                    type: "method",
                    id: child.id,
                    position,
                    data: {
                        id: child.id,
                        name: child.name,
                        qname: child.qname || "",
                        inputs: child.inputs,
                        outputs: child.outputs,
                        callOrder: (child.call_order as number) ?? 0,
                        icon: child.icon,
                        theme: nodeTheme,
                        isExpandable: isExpandable,
                        isSelected: selectedNode?.id === child.id,
                    },
                });
            } else if (child.node_type === "function") {
                nodes.push({
                    type: "function",
                    id: child.id,
                    position,
                    data: {
                        id: child.id,
                        name: child.name,
                        qname: child.qname || "",
                        inputs: child.inputs,
                        outputs: child.outputs,
                        callOrder: (child.call_order as number) ?? 0,
                        icon: child.icon,
                        theme: nodeTheme,
                        isExpandable: isExpandable,
                        isSelected: selectedNode?.id === child.id,
                    },
                });
            }
        });

        // Add END circle node
        if (!isDefinitionNode) {
            nodes.push({
                type: "circle",
                id: `__end__-${node.id}`,
                position: { x: ordered.length * 420, y: 0 },
                data: { label: "End", kind: "end" },
            } as unknown as Node);
        }

        return nodes;
    }, [selectedFromSources, selectedNode?.isExpanded, selectedNode?.id]);


    const initialEdges = useMemo((): Edge[] => {
        if (!initialNodes || initialNodes.length === 0) return [];
        const startNode = initialNodes.find((n) => n.type === "circle" && n.id.startsWith("__start__"));
        const endNode = initialNodes.find((n) => n.type === "circle" && n.id.startsWith("__end__"));
        const dataNodes = initialNodes
            .filter((n) => n.type !== "circle")
            .sort((a, b) => (a.position?.x ?? 0) - (b.position?.x ?? 0));

        const sequenceIds: string[] = [];
        if (startNode) sequenceIds.push(startNode.id);
        sequenceIds.push(...dataNodes.map((n) => n.id));
        if (endNode) sequenceIds.push(endNode.id);

        const edges: Edge[] = [];
        for (let i = 0; i < sequenceIds.length - 1; i++) {
            const source = sequenceIds[i];
            const target = sequenceIds[i + 1];
            edges.push({
                id: `e-${source}-${target}`,
                source,
                target,
                type: "smartEdge",
            });
        }
        return edges;
    }, [initialNodes]);
    const onNodesChange = useCallback(() => { }, []);
    const onEdgesChange = useCallback(() => { }, []);

    const onConnect = useCallback(
        (setEdges: (updater: Edge[] | ((eds: Edge[]) => Edge[])) => void): OnConnect =>
            (connection: Connection) => setEdges((eds) => addEdge({ ...connection, type: "smartEdge" }, eds)),
        []
    );

    return {
        initialNodes,
        doNotReRenderCanvas: selectedNode?.doNotReRenderCanvas,
        initialEdges,
        selected: selectedFromSources.node,
        parent: selectedFromSources.parent,
        onNodesChange,
        onEdgesChange,
        onConnect,
    };
}