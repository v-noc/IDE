import React from "react";
import { TreeNode } from "./TreeNode";
import type { ProjectNode } from "@/types/project";

// Sample project data for placeholder
const sampleProjectData: ProjectNode = {
  id: "root",
  name: "Sample Project",
  icon: "Folder",
  iconColor: "#3b82f6",
  cardColor: "#eff6ff",
  children: [
    {
      id: "src",
      name: "src",
      icon: "Folder",
      iconColor: "#f59e0b",
      children: [
        {
          id: "components",
          name: "components",
          icon: "Folder",
          iconColor: "#10b981",
          children: [
            {
              id: "button",
              name: "Button.tsx",
              icon: "Code",
              iconColor: "#8b5cf6",
            },
            {
              id: "input",
              name: "Input.tsx",
              icon: "Code",
              iconColor: "#8b5cf6",
            },
          ],
        },
        {
          id: "utils",
          name: "utils",
          icon: "Folder",
          iconColor: "#10b981",
          children: [
            {
              id: "helpers",
              name: "helpers.ts",
              icon: "FileText",
              iconColor: "#06b6d4",
            },
          ],
        },
      ],
    },
    {
      id: "package",
      name: "package.json",
      icon: "Package",
      iconColor: "#ef4444",
    },
  ],
};

const ProjectTree = () => {
  return (
    <div>
      <ul className="space-y-1">
        <TreeNode node={sampleProjectData} />
      </ul>
    </div>
  );
};

export default ProjectTree;
