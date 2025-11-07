import { useEffect, useMemo } from "react";
import type {
  AnyNodeTree,
  CallNodeTree,
  ContainerNodeTree,
} from "@/types/project";
import { TreeNode } from "./TreeNode";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";

// Collect ancestor keys path to a target key
const collectAncestorKeys = (root: AnyNodeTree, key: string): string[] => {
  const path: string[] = [];
  const dfs = (node: AnyNodeTree): boolean => {
    path.push(node._key);
    if (node._key === key) return true;
    if (node.children) {
      for (const child of node.children as AnyNodeTree[]) {
        if (dfs(child)) return true;
      }
    }
    path.pop();
    return false;
  };
  dfs(root);
  // drop self; we only need ancestors to expand
  path.pop();
  return path;
};

// Determines whether a child node should be rendered in the tree.
// Rules:
// 1) Exclude all nodes whose node_type is "call".
// 2) If the node is a "group", exclude it only when its group_type is "call".
// 3) Allow all other node types.
const shouldRenderChild = (node: ContainerNodeTree): boolean => {
  // Exclude direct call nodes
  if (node.node_type === "call") return false;
  // For group nodes, exclude only if the group's type is "call"
  if (node.node_type === "group") {
    if ("group_type" in node) {
      return (node as { group_type: string }).group_type !== "call";
    }
    // If group_type is absent, treat it as renderable
    return true;
  }
  // Allow all other node types
  return true;
};

const ProjectTree = ({ projectTree }: { projectTree: AnyNodeTree }) => {
  const {
    selectedNode,
    focusedNode,
    focusStack,
    popFocus,
    clearFocus,
    expandedNodeIds,
    toggleNodeExpansion,
    setSelectedNode,
  } = useProjectStore();

  // When a call is selected, auto-select and scroll to its target; expand ancestors
  const targetKey = useMemo(() => {
    if (selectedNode?.node_type === "call") {
      const target = (selectedNode as CallNodeTree).target;
      return target?._key ?? null;
    }
    return null;
  }, [selectedNode]);

  useEffect(() => {
    if (!targetKey || !projectTree) return;

    // Expand ancestors of the target
    const ancestorKeys = collectAncestorKeys(projectTree, targetKey);
    for (const key of ancestorKeys) {
      if (!expandedNodeIds.includes(key)) {
        toggleNodeExpansion(key);
      }
    }

    const el = document.querySelector(`[data-node-key="${targetKey}"]`);
    if (el && "scrollIntoView" in el) {
      (el as HTMLElement).scrollIntoView({
        block: "center",
        behavior: "smooth",
      });
    }
  }, [
    targetKey,
    projectTree,
    expandedNodeIds,
    toggleNodeExpansion,
    setSelectedNode,
  ]);

  return (
    <div className="space-y-1">
      {focusedNode && (
        <div className="flex items-center justify-between px-2 py-1 bg-muted/40 border rounded">
          <div className="text-xs text-muted-foreground truncate">
            Focus: {focusStack.map((n) => n.name).join(" / ")}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="text-xs px-2 py-0.5 rounded border hover:bg-accent"
              onClick={popFocus}
            >
              Back
            </button>
            <button
              type="button"
              className="text-xs px-2 py-0.5 rounded border hover:bg-accent"
              onClick={clearFocus}
            >
              Clear
            </button>
          </div>
        </div>
      )}
      <ul className="space-y-1">
        <TreeNode
          node={(focusedNode ?? projectTree) as unknown as ContainerNodeTree}
          childFilter={shouldRenderChild}
        />
      </ul>
    </div>
  );
};

export default ProjectTree;
