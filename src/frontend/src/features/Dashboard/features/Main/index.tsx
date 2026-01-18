import { useEffect, useRef, useState } from "react";
import type { ImperativePanelHandle } from "react-resizable-panels";

import { useWorkspaceState } from "./hooks/useWorkspaceState";
import { useWorkspaceActions } from "./hooks/useWorkspaceActions";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { ProjectStore } from "@/features/Dashboard/store/useProjectStore";
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
  const isDocSidebarOpen = useProjectStore((s: ProjectStore) => s.isDocSidebarOpen[tabId]);
  const setDocSidebarOpen = useProjectStore((s: ProjectStore) => s.setDocSidebarOpen);
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

  // Close sidebar when the node changes (unless we are in the docs tab)
  useEffect(() => {
    if (tabValue !== "docs") {
      setDocSidebarOpen(tabId, false);
    }
  }, [effectiveNode?._key, tabId, tabValue]);

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
        tabValue !== "docs" && documents.length > 0 && isDocSidebarOpen ? (
          <DocSidebar
            documents={documents}
            selectedDocumentId={activeDocId}
            onSelectDocument={selectDocument}
            onDocumentChange={handleDocumentChange}
            onClose={() => setDocSidebarOpen(tabId, false)}
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
