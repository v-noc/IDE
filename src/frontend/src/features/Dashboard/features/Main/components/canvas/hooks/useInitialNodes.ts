import { useMemo } from "react";
import type { Node } from "@xyflow/react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { getNodeStyle } from "@/features/Dashboard/utils";
import type { CommonVNode, SelectedFromSources } from "./utils/types";

export function useInitialNodes(selectedFromSources: SelectedFromSources): Node[] {
    const selectedNode = useProjectStore((s) => s.selectedNode);

    return useMemo((): Node[] => {
        const { node, parent } = selectedFromSources;
        if (!node) return [];

        let nodesToBeRender: CommonVNode[] | null = null;
        let isDefinitionNode = false;

        if (parent == null || !["class", "function"].includes(parent.node_type as string)) {
            if (selectedNode?.isExpanded) {
                nodesToBeRender = node.children;
            } else {
                isDefinitionNode = true;
                nodesToBeRender = [node];
            }
        } else if (parent != null && ["class", "function"].includes(parent.node_type as string)) {
            if (selectedNode?.isExpanded) {
                nodesToBeRender = node.children;
            } else {
                nodesToBeRender = parent.children;
            }
        }

        if (nodesToBeRender == null) return [];
        const ordered = [...nodesToBeRender].sort((a, b) => {
            const ao = a.call_order ?? Number.POSITIVE_INFINITY;
            const bo = b.call_order ?? Number.POSITIVE_INFINITY;
            return ao - bo;
        });

        const nodes: Node[] = [];

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
                const derivedMethods = child.methods && child.methods.length > 0
                    ? child.methods
                    : child.children.filter((c) => c.node_type === "function");

                nodes.push({
                    type: "class",
                    id: child.id,
                    position,
                    data: {
                        id: child.id,
                        name: child.name,
                        qname: child.qname || "",
                        fields: child.fields,
                        methods: derivedMethods.map((m) => ({ ...m, theme: getNodeStyle(m as any) })),
                        sourceFile: child.qname || "",
                        icon: child.icon,
                        theme: nodeTheme,
                        isExpandable: isExpandable,
                        isSelected: selectedNode?.id === child.id,
                    },
                } as unknown as Node);
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
                } as unknown as Node);
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
                } as unknown as Node);
            }
        });

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
}


