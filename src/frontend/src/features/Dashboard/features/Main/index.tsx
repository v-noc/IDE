import { useEffect, useMemo, useRef, useState } from "react";
import type { ImperativePanelHandle } from "react-resizable-panels";

import { useWorkspaceState } from "./hooks/useWorkspaceState";
import { useWorkspaceActions } from "./hooks/useWorkspaceActions";
import { WorkspaceHeader } from "./components/WorkspaceHeader";
import { WorkspaceTabs } from "./components/WorkspaceTabs";
import { WorkspaceLayout } from "./components/WorkspaceLayout";
import { useGetDocuments } from "./service/useDocuments";
import useProjectStore from "../../store/useProjectStore";
import type { CallNodeTree } from "@/types/project";

/**
 * Workspace Container - Manages the state, logic, and data flow for the central central area.
 * Composes presentational components to render the UI.
 */
interface WorkspaceProps {
  tabId: string;
}

const Workspace = ({ tabId }: WorkspaceProps) => {
  const selectedDocumentId = useProjectStore((s) => s.selectedDocumentId[tabId]);
  const setSelectedDocumentId = useProjectStore((s) => s.setSelectedDocumentId);

  // 1. Logic & State hooks
  const { effectiveNode, displayPath, suffixName, isCodeActive, selectedNode, secondarySelectedNode } = useWorkspaceState(tabId);
  const { handlePromote, updateDocumentDebounced } = useWorkspaceActions(tabId);

  const [tabValue, setTabValue] = useState("docs");
  const [isSandboxOpen, setIsSandboxOpen] = useState(true);
  const bottomPanelRef = useRef<ImperativePanelHandle>(null);

  // 2. Data Fetching
  const nodeKey = effectiveNode?._key || "";
  const { data: documents = [] } = useGetDocuments(nodeKey);

  // 3. Effects
  useEffect(() => {
    if (isCodeActive === false && tabValue === "code") {
      setTabValue("docs");
    }
  }, [effectiveNode, isCodeActive, tabValue]);

  useEffect(() => {
    const currentSelected = secondarySelectedNode
      ? (secondarySelectedNode as CallNodeTree)?.target ?? selectedNode
      : selectedNode;

    if (
      (!selectedDocumentId ||
        !currentSelected?.documents.includes(`documents/${selectedDocumentId}`)) &&
      documents.length > 0
    ) {
      setSelectedDocumentId(tabId, documents[0]._key);
    }
  }, [tabId, documents, selectedDocumentId, selectedNode, secondarySelectedNode, setSelectedDocumentId]);

  // Derived content
  const selectedDocument = useMemo(
    () => documents.find((d) => d._key === selectedDocumentId) || null,
    [documents, selectedDocumentId]
  );

  // 4. Sync panel collapsed state
  useEffect(() => {
    const panel = bottomPanelRef.current;
    if (!panel) return;
    if (isSandboxOpen && panel.isCollapsed()) {
      panel.expand();
    } else if (!isSandboxOpen && !panel.isCollapsed()) {
      panel.collapse();
    }
  }, [isSandboxOpen]);

  return (
    <WorkspaceLayout
      bottomPanelRef={bottomPanelRef}
      isSandboxOpen={isSandboxOpen}
      onToggleSandbox={setIsSandboxOpen}
      topPanelContent={
        <WorkspaceTabs
          isCodeActive={isCodeActive}
          tabValue={tabValue}
          onTabValueChange={setTabValue}
          selectedDocument={selectedDocument}
          onDocumentChange={(data) => {
            if (selectedDocumentId) {
              updateDocumentDebounced.call({
                id: selectedDocument?._key || "",
                data,
              });
            }
          }}
          headerSlot={
            <WorkspaceHeader
              displayPath={displayPath}
              suffixName={suffixName}
              onPromote={handlePromote}
            />
          }
        />
      }
    />
  );
};

export default Workspace;
