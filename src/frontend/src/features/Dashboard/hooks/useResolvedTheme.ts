import { useMemo } from "react";
import type { ThemeConfig, AnyNodeTree, ProjectNodeTree } from "@/types/project";
import useProjectStore from "../store/useProjectStore";

const THEME_KEYS: (keyof ThemeConfig)[] = [
  "navbarColor",
  "leftSidebarColor",
  "rightSidebarColor",
  "backgroundColor",
  "textColor",
  "iconColor",
  "cardColor",
];

const hasEffectiveTheme = (t: ThemeConfig | undefined): boolean => {
  if (!t) return false;
  return THEME_KEYS.some((key) => Boolean(t[key]));
}

function normalizeTheme(t: ThemeConfig | undefined | null): ThemeConfig | undefined {
  if (!t) return undefined;
  const normalized: ThemeConfig = {};
  for (const key of THEME_KEYS) {
    const value = t[key] as unknown as string | undefined | null;
    if (value) normalized[key] = value;
  }
  return hasEffectiveTheme(normalized) ? normalized : undefined;
}

function mergeThemes(base: ThemeConfig | undefined, override: ThemeConfig | undefined): ThemeConfig {
  const result: ThemeConfig = { ...(base ?? {}) };
  for (const key of THEME_KEYS) {
    const value = override?.[key];
    if (value) result[key] = value;
  }
  return result;
}

function findSelectedPath(
  root: ProjectNodeTree | null,
  selected: AnyNodeTree | null): AnyNodeTree[] {
  if (!root || !selected) return [];

  const dfs = (node: AnyNodeTree, acc: AnyNodeTree[]): boolean => {
    acc.push(node);
    if (node._id === selected._id) return true;
    if (node.children) {
      for (const child of node.children as AnyNodeTree[]) {
        if (dfs(child, acc)) return true;
      }
    }
    acc.pop();
    return false;
  };

  const path: AnyNodeTree[] = [];
  if (dfs(root, path)) return path;
  return [];
}

export function useResolvedTheme() {
  const projectData = useProjectStore((s) => s.projectData);
  const selectedNode = useProjectStore((s) => s.selectedNode);

  const selectedPath = useMemo(() => {
    if (!projectData || !selectedNode) return [];
    return findSelectedPath(projectData, selectedNode);
  }, [projectData, selectedNode]);

  const theme = useMemo(() => {
    if (selectedNode && selectedPath.length > 0) {
      let merged: ThemeConfig | undefined = undefined;
      for (const node of selectedPath) {
        merged = mergeThemes(merged, normalizeTheme(node.theme_config));
      }
      return hasEffectiveTheme(merged) ? merged : undefined;
    }
    const projectTheme = normalizeTheme(projectData?.theme_config);
    return hasEffectiveTheme(projectTheme) ? projectTheme : undefined;

  }, [selectedNode, selectedPath, projectData?.theme_config]);

  const cssVariables: React.CSSProperties = theme ? {
    "--navbar-color": theme.navbarColor,
    "--left-sidebar-color": theme.leftSidebarColor,
    "--right-sidebar-color": theme.rightSidebarColor,
    "--background-color": theme.backgroundColor,
    "--text-color": theme.textColor,
    "--icon-color": theme.iconColor,
    "--card-color": theme.cardColor,
  } : {};
  return { theme, cssVariables };
}
