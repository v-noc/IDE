import type { AnyNodeTree } from "@/types/project";
import { TreeNode } from "./TreeNode";

const ProjectTree = ({ projectTree }: { projectTree: AnyNodeTree }) => {
  return (
    <ul className="space-y-1">
      <TreeNode
        node={projectTree}
        childFilter={(node) => node.node_type !== "call"}
      />
    </ul>
  );
};

export default ProjectTree;
