import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";
import { TreeNode } from "./TreeNode";

const ProjectTree = ({ projectTree }: { projectTree: ProjectTreeResponse }) => {
  return (
    <ul className="space-y-1">
      <TreeNode node={projectTree} />
    </ul>
  );
};

export default ProjectTree;
