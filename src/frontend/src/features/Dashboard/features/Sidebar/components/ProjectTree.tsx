import { useEffect, useMemo } from "react";
import type { AnyNodeTree, CallNodeTree } from "@/types/project";
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

    // Select the target node
    const selectTarget = (node: AnyNodeTree): AnyNodeTree | null => {
      if (node._key === targetKey) return node;
      if (node.children) {
        for (const child of node.children as AnyNodeTree[]) {
          const found = selectTarget(child);
          if (found) return found;
        }
      }
      return null;
    };
    const foundTarget = selectTarget(projectTree);
    if (foundTarget) setSelectedNode(foundTarget);

    // Scroll it into view after next paint
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

  const rootToRender = focusedNode ?? projectTree;

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
          node={rootToRender}
          childFilter={(node) => node.node_type !== "call"}
        />
      </ul>
    </div>
  );
};

export default ProjectTree;
