import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";

type NodeWithChildren = AnyNodeTree & { children?: AnyNodeTree[] };

export function findNodeByKey(
    root: ProjectNodeTree | null | undefined,
    key: string
): AnyNodeTree | null {
    if (!root || !key) return null;
    const stack: AnyNodeTree[] = [root];
    while (stack.length) {
        const node = stack.pop() as AnyNodeTree;
        if (node._key === key) return node;
        const children = (node as NodeWithChildren).children;
        if (Array.isArray(children) && children.length) {
            for (let i = children.length - 1; i >= 0; i -= 1) {
                stack.push(children[i]);
            }
        }
    }
    return null;
}

export function findNodeById(
    root: ProjectNodeTree | null | undefined,
    id: string
): AnyNodeTree | null {
    if (!root || !id) return null;
    const stack: AnyNodeTree[] = [root];
    while (stack.length) {
        const node = stack.pop() as AnyNodeTree;
        if (node._id === id) return node;
        const children = (node as NodeWithChildren).children;
        if (Array.isArray(children) && children.length) {
            for (let i = children.length - 1; i >= 0; i -= 1) {
                stack.push(children[i]);
            }
        }
    }
    return null;
}
export function findNodeLineage(
    root: ProjectNodeTree | null | undefined,
    key: string
): AnyNodeTree[] | null {
    if (!root || !key) return null;

    const lineage: AnyNodeTree[] = [];

    function search(node: AnyNodeTree): boolean {
        lineage.push(node);
        if (node._key === key) return true;

        const children = (node as NodeWithChildren).children;
        if (Array.isArray(children)) {
            for (const child of children) {
                if (search(child)) return true;
            }
        }

        lineage.pop();
        return false;
    }

    if (search(root)) {
        return lineage;
    }
    return null;
}
