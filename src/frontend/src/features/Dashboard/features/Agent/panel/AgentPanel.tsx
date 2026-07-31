import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { findNodeByKey } from "@/features/Dashboard/utils/findNode";
import { useRunStream } from "../hooks/useRunStream";
import type { NodeRefPart } from "../stream/types";
import { Composer } from "../composer/Composer";
import { ChatThread } from "../thread/ChatThread";
import { PanelHeader } from "./PanelHeader";

export function AgentPanel() {
  const { conversation, streamError } = useRunStream();
  const activeTabId = useTabStore((s) => s.activeTabId);
  const projectData = useProjectStore((s) => s.projectData);
  const setSelectedNode = useProjectStore((s) => s.setSelectedNode);

  const focusNode = (part: NodeRefPart) => {
    if (!projectData) return;
    const node = findNodeByKey(projectData, part.node_id);
    if (node) setSelectedNode(activeTabId, node);
  };

  return (
    <div className="agent-v2 flex h-full w-full min-w-[420px] flex-col border-l border-agent-border bg-agent-bg-panel">
      <PanelHeader conversationStatus={conversation?.status} />
      <ChatThread
        conversation={conversation}
        connectionError={streamError}
        onFocusNode={focusNode}
      />
      <Composer onFocusNode={focusNode} />
    </div>
  );
}
