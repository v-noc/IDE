import type { ProjectNodeTree } from "@/types/project";
import { TreeNode } from "./TreeNode";

const ProjectTree = ({ projectTree }: { projectTree: ProjectNodeTree }) => {
  return (
    <ul className="space-y-1">
      <TreeNode node={projectTree} />
    </ul>
  );
};

export default ProjectTree;
