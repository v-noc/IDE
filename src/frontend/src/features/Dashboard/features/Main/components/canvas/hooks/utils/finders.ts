import type { CommonVNode } from "./types";

export function findNodeAndParentByKey(
    root: CommonVNode,
    id: string
): { node: CommonVNode | null; parent: CommonVNode | null } {
    if (root.id === id) return { node: root, parent: null };
    let found: CommonVNode | null = null;
    let parent: CommonVNode | null = null;
    const walk = (n: CommonVNode) => {
        for (const c of n.children || []) {
            if (c.id === id && (c.node_type === "class" || c.node_type === "function")) {
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


