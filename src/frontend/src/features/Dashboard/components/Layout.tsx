import { ResizableHandle, ResizablePanel } from "@/components/ui/resizable";
import { useEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ImperativePanelHandle } from "react-resizable-panels";
import { useThemeStore } from "../store/useThemeStore";
import type { ThemeConfig } from "@/types/project";

import useProjectStore from "../store/useProjectStore";
import type { ProjectNodeTree, ContainerNodeTree } from "@/types/project";

const hasEffectiveTheme = (t: ThemeConfig | undefined): boolean => {
  if (!t) return false;
  const values = [
    t.navbarColor,
    t.leftSidebarColor,
    t.rightSidebarColor,
    t.backgroundColor,
    t.textColor,
    t.iconColor,
    t.cardColor,
  ];
  return values.some((v) => Boolean(v));
};

const THEME_KEYS: (keyof ThemeConfig)[] = [
  "navbarColor",
  "leftSidebarColor",
  "rightSidebarColor",
  "backgroundColor",
  "textColor",
  "iconColor",
  "cardColor",
];

const normalizeTheme = (
  t: ThemeConfig | undefined | null
): ThemeConfig | undefined => {
  if (!t) return undefined;
  const normalized: ThemeConfig = {};
  for (const key of THEME_KEYS) {
    const value = t[key] as unknown as string | undefined | null;
    if (value) normalized[key] = value;
  }
  return hasEffectiveTheme(normalized) ? normalized : undefined;
};

const mergeThemes = (
  baseTheme: ThemeConfig | undefined,
  overrideTheme: ThemeConfig | undefined
): ThemeConfig => {
  const result: ThemeConfig = { ...(baseTheme ?? {}) };
  for (const key of THEME_KEYS) {
    const value = overrideTheme?.[key];
    if (value) result[key] = value;
  }
  return result;
};

const Layout = ({
  main,
  navbar,
  leftSidebar,
  rightSidebar,
}: {
  main: React.ReactNode;
  navbar: React.ReactNode;
  leftSidebar: React.ReactNode;
  rightSidebar?: React.ReactNode;
}) => {
  const [isRightOpen, setIsRightOpen] = useState(true);
  const [isLeftOpen, setIsLeftOpen] = useState(true);
  const leftPanelRef = useRef<ImperativePanelHandle>(null);

  // Sync panel collapsed state with our local boolean
  useEffect(() => {
    const panel = leftPanelRef.current;
    if (!panel) return;
    if (isLeftOpen && panel.isCollapsed()) {
      panel.expand();
    } else if (!isLeftOpen && !panel.isCollapsed()) {
      panel.collapse();
    }
  }, [isLeftOpen]);
  const { theme, setTheme } = useThemeStore();
  const { projectData, selectedNode } = useProjectStore();

  const selectedPath = useMemo(() => {
    // Returns path from root to selected node (inclusive)
    const path: ContainerNodeTree[] = [];
    if (!projectData || !selectedNode) return path;

    const dfs = (node: ContainerNodeTree, acc: ProjectNodeTree[]): boolean => {
      acc.push(node);
      if (node.id === selectedNode.id) return true;
      if (node.children) {
        for (const child of node.children) {
          if (dfs(child, acc)) return true;
        }
      }
      acc.pop();
      return false;
    };

    const tmp: ContainerNodeTree[] = [];
    if (dfs(projectData, tmp)) return tmp;
    return [];
  }, [projectData, selectedNode]);

  const resolvedTheme = useMemo(() => {
    // Merge themes along the path from root to selected node, allowing child to override
    if (selectedNode && selectedPath.length > 0) {
      let merged: ThemeConfig | undefined = undefined;
      for (const node of selectedPath) {
        merged = mergeThemes(merged, normalizeTheme(node.theme_config));
      }
      return hasEffectiveTheme(merged) ? merged : undefined;
    }

    // No node found in project tree; do not override externally set theme
    if (selectedNode && selectedPath.length === 0) {
      return undefined;
    }

    // No node selected → use project theme if available and non-empty
    const projectTheme = normalizeTheme(projectData?.theme_config);
    return hasEffectiveTheme(projectTheme) ? projectTheme : undefined;
  }, [selectedNode, selectedPath, projectData?.theme_config]);

  useEffect(() => {
    if (resolvedTheme !== undefined) {
      setTheme(resolvedTheme);
    }
  }, [resolvedTheme, setTheme]);

  const style = theme
    ? ({
        "--navbar-color": theme.navbarColor,
        "--left-sidebar-color": theme.leftSidebarColor,
        "--right-sidebar-color": theme.rightSidebarColor,
        "--background-color": theme.backgroundColor,
        "--text-color": theme.textColor,
        "--icon-color": theme.iconColor,
        "--card-color": theme.cardColor,
      } as React.CSSProperties)
    : {};

  return (
    <div
      className="relative flex min-h-screen max-h-screen w-full h-full"
      style={style}
    >
      {/* Left Sidebar (always mounted; collapsed via imperative API) */}
      <ResizablePanel
        ref={leftPanelRef}
        defaultSize={20}
        collapsible
        collapsedSize={0}
        minSize={12}
        className="relative bg-[var(--left-sidebar-color)] group"
      >
        {/* Edge-centered toggle to collapse */}
        <button
          type="button"
          aria-label="Close left sidebar"
          onClick={() => setIsLeftOpen(false)}
          className="absolute -right-3 top-1/2 z-50 -translate-y-1/2 rounded-md border bg-background/80 p-1 py-2 shadow hover:bg-accent opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
        >
          <ChevronLeft className="h-4 w-4 -translate-x-1" />
        </button>
        {leftSidebar}
      </ResizablePanel>
      {/* Minimal handle: only color changes on hover */}
      <ResizableHandle className="w-px px-0 border-l border-transparent hover:border-border hover:bg-border/20 transition-colors duration-150" />
      {/* When left is closed, show open toggle */}
      {!isLeftOpen && (
        <button
          type="button"
          aria-label="Open left sidebar"
          onClick={() => setIsLeftOpen(true)}
          className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-2 z-50 p-1 py-2 bg-white border rounded-r-md shadow hover:bg-gray-50"
        >
          <ChevronRight className="h-4 w-4 translate-x-1" />
        </button>
      )}
      {/* Main Content Area */}
      <ResizablePanel
        defaultSize={rightSidebar ? 60 : 80}
        className="flex-1 flex flex-col w-full bg-[var(--background-color)]"
      >
        {/* Navbar */}
        <nav className="p-2 border-b shadow-sidebar bg-[var(--navbar-color)]">
          {navbar}
        </nav>

        {/* Content */}
        <main className="flex-1 min-h-0 h-full">{main}</main>
      </ResizablePanel>

      {/* Right Sidebar (collapsible) */}
      {/* {rightSidebar && isRightOpen && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel
            defaultSize={20}
            minSize={12}
            collapsible
            className="bg-[var(--right-sidebar-color)]"
          >
            {rightSidebar}
          </ResizablePanel>
        </>
      )} */}

      {/* Re-open toggle button when right sidebar is hidden */}
      {rightSidebar && !isRightOpen && (
        <button
          type="button"
          aria-label="Open right sidebar"
          onClick={() => setIsRightOpen(true)}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-50 p-2 bg-white border rounded-l-md shadow hover:bg-gray-50"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
      )}

      {/* Provide a way for the sidebar content to close itself via context (simple prop function) */}
      {/* Consumers can pass a button that calls the provided onClose if desired */}
    </div>
  );
};

export default Layout;
