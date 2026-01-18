import { useEffect, useRef, useState } from "react";
import type { ImperativePanelHandle } from "react-resizable-panels";

import { useWorkspaceState } from "./hooks/useWorkspaceState";
import { useWorkspaceActions } from "./hooks/useWorkspaceActions";
import { WorkspaceHeader } from "./components/WorkspaceHeader";
import { WorkspaceTabs } from "./components/WorkspaceTabs";
import { WorkspaceLayout } from "./components/WorkspaceLayout";
import { DocSidebar } from "./components/Docs/DocSidebar";
import { useWorkspaceDocs } from "./hooks/useWorkspaceDocs";

/**
 * Workspace Container - Manages the state, logic, and data flow for the central central area.
 * Composes presentational components to render the UI.
 */
interface WorkspaceProps {
  tabId: string;
}

const Workspace = ({ tabId }: WorkspaceProps) => {
  // 1. Logic & State hooks
  const { effectiveNode, displayPath, isCodeActive, selectedNode, secondarySelectedNode } = useWorkspaceState(tabId);
  const { handlePromote } = useWorkspaceActions(tabId);

  const [tabValue, setTabValue] = useState("docs");
  const [isSandboxOpen, setIsSandboxOpen] = useState(true);
  const bottomPanelRef = useRef<ImperativePanelHandle>(null);

  // 2. Docs logic (using React 19 rules & useEffectEvent)
  const {
    documents,
    selectedDocumentId: activeDocId,
    selectedDocument,
    handleDocumentChange,
    selectDocument,
  } = useWorkspaceDocs(tabId, effectiveNode, selectedNode, secondarySelectedNode);

  // 3. Effects
  useEffect(() => {
    if (isCodeActive === false && tabValue === "code") {
      setTabValue("docs");
    }
  }, [effectiveNode, isCodeActive, tabValue]);

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
      tabId={tabId}
      bottomPanelRef={bottomPanelRef}
      isSandboxOpen={isSandboxOpen}
      onToggleSandbox={setIsSandboxOpen}
      rightSidebarContent={
        tabValue !== "docs" ? (
          <DocSidebar
            documents={documents}
            selectedDocumentId={activeDocId}
            onSelectDocument={selectDocument}
            onDocumentChange={handleDocumentChange}
          />
        ) : undefined
      }
      topPanelContent={
        <WorkspaceTabs
          tabId={tabId}
          isCodeActive={isCodeActive}
          tabValue={tabValue}
          onTabValueChange={setTabValue}
          selectedDocument={selectedDocument}
          onDocumentChange={handleDocumentChange}
          headerSlot={
            <WorkspaceHeader
              displayPath={displayPath}
              showPromote={Boolean(secondarySelectedNode)}
              onPromote={handlePromote}
            />
          }
        />
      }
    />
  );
};

export default Workspace;
