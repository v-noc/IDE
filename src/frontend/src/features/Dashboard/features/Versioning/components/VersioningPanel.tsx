import React from "react";
import { X } from "lucide-react";
import { useVersioningStore } from "../store/useVersioningStore";
import CommitHistory from "./CommitHistory";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useCommitHistory } from "../hooks/useCommitHistory";

const VersioningPanel: React.FC<{ tabId: string }> = ({ tabId }) => {
  const { togglePanel } = useVersioningStore();
  const { projectData, selectedNode, secondarySelectedNode } =
    useProjectStore();

  const nodeId = secondarySelectedNode?.[tabId] || selectedNode?.[tabId];

  const { data: commits } = useCommitHistory(projectData?.id, nodeId?.id);
  console.log(commits);
  console.log(nodeId, " ", projectData?.id);

  return (
    <div className="flex h-full w-full flex-col border-l bg-white shadow-sm transition-all duration-300">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h2 className="text-lg font-semibold text-slate-800">Commit history</h2>
        <button
          onClick={togglePanel}
          className="rounded-md p-1 hover:bg-slate-100 text-slate-500"
        >
          <X size={20} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        <CommitHistory />
      </div>
    </div>
  );
};

export default VersioningPanel;
