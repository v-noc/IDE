import Layout from "@/features/Dashboard/components/Layout";
import SideBar from "@/features/Dashboard/features/Sidebar/components/SideBar";
import Navbar from "@/features/Dashboard/features/Navbar/componets/Navbar";
import MainCanvas from "@/features/Dashboard/features/Main";
import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";

import { ResizablePanelGroup } from "@/components/ui/resizable";
import MainWithRightSidebar from "@/features/Dashboard/features/Main/MainWithRightSidebar";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { initSocket, disconnectSocket } from "@/services/socket";

// Recursively check if any Group node exists
function containsGroup(node: AnyNodeTree): boolean {
  if (node.node_type === "group") return true;
  const children =
    (node as unknown as { children?: AnyNodeTree[] }).children ?? [];
  for (const child of children) {
    if (containsGroup(child)) return true;
  }
  return false;
}

// Flatten Group nodes by lifting their children to the parent level
function flattenGroups(node: AnyNodeTree): AnyNodeTree[] {
  if (node.node_type === "group") {
    // Replace the group node with its flattened children
    const flattened: AnyNodeTree[] = [];
    const children =
      (node as unknown as { children?: AnyNodeTree[] }).children ?? [];
    for (const child of children) {
      flattened.push(...flattenGroups(child));
    }
    return flattened;
  }
  const cloneObj = {
    ...(node as unknown as Record<string, unknown>),
  } as unknown;
  const clone = cloneObj as AnyNodeTree;
  const children =
    (node as unknown as { children?: AnyNodeTree[] }).children ?? [];
  if (children.length > 0) {
    const newChildren: AnyNodeTree[] = [];
    for (const child of children) {
      newChildren.push(...flattenGroups(child));
    }
    // Cast to preserve specific child unions for each node kind
    (clone as unknown as { children?: AnyNodeTree[] }).children =
      newChildren as unknown as AnyNodeTree[];
  }
  return [clone];
}

// Create a short token from the first UUID found in the _key.
// If a UUID is found, return its 4th hyphen-separated segment; otherwise fallback to first 6 chars.
function extractShortFocusToken(key: string): string {
  const uuidRegex =
    /([0-9a-fA-F]{8})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{12})/;
  const match = key.match(uuidRegex);
  if (match) {
    return match[4];
  }
  return key.slice(0, 6);
}

function findNodeByFocusToken(
  root: AnyNodeTree,
  token: string
): AnyNodeTree | null {
  const stack: AnyNodeTree[] = [root];
  while (stack.length > 0) {
    const node = stack.pop() as AnyNodeTree;
    if (extractShortFocusToken(node._key) === token) return node;
    const children =
      (node as unknown as { children?: AnyNodeTree[] }).children ?? [];
    for (let i = children.length - 1; i >= 0; i--) {
      stack.push(children[i]);
    }
  }
  return null;
}

const Dashboard = () => {
  const {
    selectedNode,
    projectData,
    setSelectedNode,
    setProjectData,
    focusStack,
    pushFocus,
    clearFocus,
  } = useProjectStore();
  const [searchParams, setSearchParams] = useSearchParams();

  // If ?disable=group is set, remove all Group nodes by lifting their children up
  useEffect(() => {
    if (projectData == null) return;
    const disable = searchParams.get("disable");
    const disableGroup = disable?.split(",").includes("group");
    if (!disableGroup) return;
    if (!containsGroup(projectData)) return;
    const flattened = flattenGroups(projectData);
    const newRoot = flattened[0] as ProjectNodeTree;
    if (newRoot && newRoot.node_type === "project") {
      setProjectData(newRoot);
    }
  }, [projectData, searchParams, setProjectData]);

  // Apply focus from URL once project data is ready (and after group flattening if enabled)
  useEffect(() => {
    if (projectData == null) return;
    const disable = searchParams.get("disable");
    const disableGroup = disable?.split(",").includes("group") ?? false;
    if (disableGroup && containsGroup(projectData)) return; // wait until flattened
    const focusParam = searchParams.get("focus");
    if (!focusParam) return;

    const target = findNodeByFocusToken(projectData, focusParam);
    if (!target) return;
    clearFocus();
    pushFocus(target);
  }, [projectData, searchParams, clearFocus, pushFocus]);

  // Keep URL 'focus' param in sync with active focus
  useEffect(() => {
    const currentFocused = focusStack[focusStack.length - 1] ?? null;
    const currentToken = currentFocused
      ? extractShortFocusToken(currentFocused._key)
      : null;
    const urlToken = searchParams.get("focus");
    if (currentToken !== urlToken) {
      const nextParams = new URLSearchParams(searchParams);
      if (currentToken) {
        nextParams.set("focus", currentToken);
      }
      setSearchParams(nextParams, { replace: true });
    }
  }, [focusStack, searchParams, setSearchParams]);

  useEffect(() => {
    if (selectedNode == null && projectData != null) {
      setSelectedNode(projectData);
    }
  }, [selectedNode, projectData, setSelectedNode]);

  // Initialize socket connection when Dashboard mounts
  useEffect(() => {
    initSocket();

    // Cleanup: disconnect socket when Dashboard unmounts
    return () => {
      disconnectSocket();
    };
  }, []);

  return (
    <ResizablePanelGroup direction="horizontal">
      <Layout
        main={<MainWithRightSidebar left={<MainCanvas />} />}
        navbar={<Navbar />}
        leftSidebar={<SideBar />}
      />
    </ResizablePanelGroup>
  );
};

export default Dashboard;
