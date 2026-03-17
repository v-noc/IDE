import { useEffect, useMemo, useRef, useState } from "react";
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
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import { useCommitHistory } from "@/features/Dashboard/features/Versioning/hooks/useCommitHistory";

/**
 * Workspace Container - Manages the state, logic, and data flow for the central central area.
 * Composes presentational components to render the UI.
 */
interface WorkspaceProps {
  tabId: string;
}

const Workspace = ({ tabId }: WorkspaceProps) => {
  // 1. Logic & State hooks
  const {
    effectiveNode,
    displayPath,
    isCodeActive,
    selectedNode,
    secondarySelectedNode,
  } = useWorkspaceState(tabId);
  const { handlePromote } = useWorkspaceActions(tabId);

  const [tabValue, setTabValue] = useState("docs");
  const [isSandboxOpen, setIsSandboxOpen] = useState(true);
  const isVersioningOpen = useVersioningStore((s) => s.isOpen);
  const setHistoryScope = useVersioningStore((s) => s.setHistoryScope);
  const clearHistoryScope = useVersioningStore((s) => s.clearHistoryScope);
  const isDocSidebarOpen = useProjectStore(
    (s: ProjectStore) => s.isDocSidebarOpen[tabId]
  );
  const setDocSidebarOpen = useProjectStore(
    (s: ProjectStore) => s.setDocSidebarOpen
  );
  const bottomPanelRef = useRef<ImperativePanelHandle>(null);

  // 2. Docs logic (using React 19 rules & useEffectEvent)
  const {
    documents,
    selectedDocumentId: activeDocId,
    selectedDocument,
    nodeKey,
    projectId,
    selectDocument,
  } = useWorkspaceDocs(
    tabId,
    effectiveNode,
    selectedNode,
    secondarySelectedNode
  );

  const historyScope = useMemo(() => {
    if (tabValue === "docs") {
      return { scopeType: "docs", scopeId: selectedDocument?.id ?? null };
    }
    if (tabValue === "code") {
      return { scopeType: "code", scopeId: nodeKey || null };
    }
    return { scopeType: tabValue, scopeId: nodeKey || null };
  }, [nodeKey, selectedDocument?.id, tabValue]);

  useEffect(() => {
    setHistoryScope(tabId, historyScope);
  }, [historyScope, setHistoryScope, tabId]);

  useEffect(() => {
    return () => {
      clearHistoryScope(tabId);
    };
  }, [clearHistoryScope, tabId]);

  useCommitHistory(projectId ?? undefined, historyScope.scopeId ?? undefined, {
    start: 0,
    count: 10,
    enabled:
      Boolean(historyScope.scopeId) &&
      (isVersioningOpen || historyScope.scopeType === "docs"),
  });

  // 3. Effects
  useEffect(() => {
    if (isCodeActive === false && tabValue === "code") {
      setTabValue("docs");
    }
  }, [effectiveNode, isCodeActive, tabValue]);

  // Sidebar state is persisted in the store (isDocSidebarOpen[tabId])
  // It will remember its open/closed state across node changes
  // We don't force close on node change - let the user control it

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
            nodeId={nodeKey}
            projectId={projectId ?? ""}
            onSelectDocument={selectDocument}
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
          nodeId={nodeKey}
          projectId={projectId ?? ""}
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
