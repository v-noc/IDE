import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { TreeNode } from "./TreeNode";
import { FocusBreadcrumb } from "./FocusBreadcrumb";
import { useAutoExpandToNode } from "../hooks/useAutoExpandToNode";
import { shouldRenderChild } from "@/features/Dashboard/utils/treeUtils";
import type { AnyNodeTree, ContainerNodeTree } from "@/types/project";

interface ProjectTreeProps {
  projectTree: AnyNodeTree;
}

export default function ProjectTree({ projectTree }: ProjectTreeProps) {
  const focusedNode = useProjectStore((s) => s.focusedNode);

  // Auto-expand when call node is selected
  useAutoExpandToNode(projectTree);

  const rootNode = (focusedNode ?? projectTree) as ContainerNodeTree;

  return (
    <div className="space-y-1">
      <FocusBreadcrumb />

      <ul className="space-y-1">
        <TreeNode node={rootNode} childFilter={shouldRenderChild} />
      </ul>
    </div>
  );
}
