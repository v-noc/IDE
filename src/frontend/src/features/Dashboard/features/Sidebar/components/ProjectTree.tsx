import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";
import { TreeNode } from "./TreeNode";

// Sample project data for placeholder

const ProjectTree = ({ projectTree }: { projectTree: ProjectTreeResponse }) => {
  return (
    <div>
      <ul className="space-y-1">
        <TreeNode node={projectTree} />
      </ul>
    </div>
  );
};

export default ProjectTree;
