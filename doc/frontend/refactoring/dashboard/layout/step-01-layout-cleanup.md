# Step 1: Layout - Extract Theme Logic

## Goal
Move theme logic out of `Layout.tsx` into a dedicated hook.

## Why
`Layout.tsx` (231 lines) mixes:
- Theme resolution logic (lines 10-56)
- Theme merging and normalization
- Panel collapse/expand state
- CSS variable generation
- JSX rendering

This makes it hard to test and maintain.

---

## Current State

```typescript
// Layout.tsx - Theme logic mixed in

const hasEffectiveTheme = (t: ThemeConfig | undefined): boolean => { ... }
const THEME_KEYS = [ ... ]
const normalizeTheme = (t: ThemeConfig | undefined | null): ThemeConfig | undefined => { ... }
const mergeThemes = (baseTheme, overrideTheme): ThemeConfig => { ... }

const Layout = ({ main, navbar, leftSidebar, rightSidebar }) => {
  const { theme, setTheme } = useThemeStore();
  const { projectData, selectedNode } = useProjectStore();
  
  // Complex path-finding logic
  const selectedPath = useMemo(() => { ... }, [...]);
  
  // Complex theme resolution
  const resolvedTheme = useMemo(() => { ... }, [...]);
  
  useEffect(() => {
    if (resolvedTheme !== undefined) {
      setTheme(resolvedTheme);
    }
  }, [resolvedTheme, setTheme]);
  
  // ... render
};
```

---

## What to Create

### NEW: `features/Dashboard/hooks/useResolvedTheme.ts`

```typescript
import { useMemo, useEffect } from 'react';
import type { AnyNodeTree, ThemeConfig, ProjectNodeTree } from '@/types/project';
import { useThemeStore } from '../store/useThemeStore';
import useProjectStore from '../store/useProjectStore';

// --- Theme utility functions ---

const THEME_KEYS: (keyof ThemeConfig)[] = [
  'navbarColor',
  'leftSidebarColor',
  'rightSidebarColor',
  'backgroundColor',
  'textColor',
  'iconColor',
  'cardColor',
];

function hasEffectiveTheme(t: ThemeConfig | undefined): boolean {
  if (!t) return false;
  return THEME_KEYS.some((key) => Boolean(t[key]));
}

function normalizeTheme(t: ThemeConfig | undefined | null): ThemeConfig | undefined {
  if (!t) return undefined;
  const normalized: ThemeConfig = {};
  for (const key of THEME_KEYS) {
    const value = t[key];
    if (value) normalized[key] = value;
  }
  return hasEffectiveTheme(normalized) ? normalized : undefined;
}

function mergeThemes(
  baseTheme: ThemeConfig | undefined,
  overrideTheme: ThemeConfig | undefined
): ThemeConfig {
  const result: ThemeConfig = { ...(baseTheme ?? {}) };
  for (const key of THEME_KEYS) {
    const value = overrideTheme?.[key];
    if (value) result[key] = value;
  }
  return result;
}

// --- Path finding ---

function findSelectedPath(
  root: ProjectNodeTree | null,
  selectedNode: AnyNodeTree | null
): AnyNodeTree[] {
  if (!root || !selectedNode) return [];

  const dfs = (node: AnyNodeTree, acc: AnyNodeTree[]): boolean => {
    acc.push(node);
    if (node._id === selectedNode._id) return true;
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

// --- Main hook ---

export function useResolvedTheme() {
  const { theme, setTheme } = useThemeStore();
  const { projectData, selectedNode } = useProjectStore();

  const selectedPath = useMemo(
    () => findSelectedPath(projectData, selectedNode),
    [projectData, selectedNode]
  );

  const resolvedTheme = useMemo(() => {
    // Merge themes along the path from root to selected node
    if (selectedNode && selectedPath.length > 0) {
      let merged: ThemeConfig | undefined = undefined;
      for (const node of selectedPath) {
        merged = mergeThemes(merged, normalizeTheme(node.theme_config));
      }
      return hasEffectiveTheme(merged) ? merged : undefined;
    }

    // No node selected → use project theme if available
    const projectTheme = normalizeTheme(projectData?.theme_config);
    return hasEffectiveTheme(projectTheme) ? projectTheme : undefined;
  }, [selectedNode, selectedPath, projectData?.theme_config]);

  // Sync to store
  useEffect(() => {
    if (resolvedTheme !== undefined) {
      setTheme(resolvedTheme);
    }
  }, [resolvedTheme, setTheme]);

  // Generate CSS variables
  const themeStyles: React.CSSProperties = theme
    ? {
        '--navbar-color': theme.navbarColor,
        '--left-sidebar-color': theme.leftSidebarColor,
        '--right-sidebar-color': theme.rightSidebarColor,
        '--background-color': theme.backgroundColor,
        '--text-color': theme.textColor,
        '--icon-color': theme.iconColor,
        '--card-color': theme.cardColor,
      }
    : {};

  return { theme, themeStyles };
}
```

---

## Update `Layout.tsx`

### Before: 231 lines
### After: ~100 lines

```diff
- import { useThemeStore } from "../store/useThemeStore";
- import type { AnyNodeTree, ThemeConfig } from "@/types/project";
- import useProjectStore from "../store/useProjectStore";
+ import { useResolvedTheme } from "../hooks/useResolvedTheme";

- const hasEffectiveTheme = (t: ThemeConfig | undefined): boolean => { ... }
- const THEME_KEYS = [ ... ]  
- const normalizeTheme = (t: ThemeConfig | undefined | null): ThemeConfig | undefined => { ... }
- const mergeThemes = (baseTheme, overrideTheme): ThemeConfig => { ... }

const Layout = ({ main, navbar, leftSidebar, rightSidebar }) => {
  const [isRightOpen, setIsRightOpen] = useState(true);
  const [isLeftOpen, setIsLeftOpen] = useState(true);
  const leftPanelRef = useRef<ImperativePanelHandle>(null);

- const { theme, setTheme } = useThemeStore();
- const { projectData, selectedNode } = useProjectStore();
- 
- const selectedPath = useMemo(() => { ... }, [...]);
- const resolvedTheme = useMemo(() => { ... }, [...]);
- 
- useEffect(() => {
-   if (resolvedTheme !== undefined) {
-     setTheme(resolvedTheme);
-   }
- }, [resolvedTheme, setTheme]);
- 
- const style = theme ? { ... } : {};
+ const { themeStyles } = useResolvedTheme();

  return (
-   <div className="..." style={style}>
+   <div className="..." style={themeStyles}>
      {/* ... rest unchanged */}
    </div>
  );
};
```

---

## Verification

- [ ] Theme still applies when selecting nodes
- [ ] Theme inheritance along path still works
- [ ] Layout.tsx is now ~100 lines
- [ ] No TypeScript errors

---

## Next Step

👉 [Step 2: Layout Composition](./step-02-layout-composition.md)
