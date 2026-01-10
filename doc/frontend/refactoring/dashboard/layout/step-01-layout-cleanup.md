# Step 1: Layout - Theme as Derived State (React 19)

## Goal
Replace `useEffect` sync with **derived state** - the modern React 19 pattern.

## Why This Matters

❌ **Old Pattern (Anti-pattern in React 19):**
```typescript
// Calculates theme, then syncs to store via useEffect
// Causes double-render: first with old value, then with new
useEffect(() => {
  if (resolvedTheme !== undefined) {
    setTheme(resolvedTheme); // Side effect!
  }
}, [resolvedTheme, setTheme]);
```

✅ **New Pattern (Derived State):**
```typescript
// Theme is calculated and returned directly
// No sync, no double-render, no tearing
const { theme, cssVariables } = useResolvedTheme();
```

---

## Key React 19 Principles

1. **No `useEffect` for state sync** - React docs explicitly advise against this
2. **Derived state** - Calculate on-the-fly, don't store duplicates
3. **CSS Variables** - Browser handles repaint, React doesn't re-render children
4. **React Compiler ready** - When you enable it, useMemo becomes optional

---

## NEW: `features/Dashboard/hooks/useResolvedTheme.ts`

```typescript
import { useMemo } from 'react';
import type { AnyNodeTree, ThemeConfig, ProjectNodeTree } from '@/types/project';
import useProjectStore from '../store/useProjectStore';

// NOTE: We removed useThemeStore. No syncing to external store.

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
  base: ThemeConfig | undefined,
  override: ThemeConfig | undefined
): ThemeConfig {
  const result: ThemeConfig = { ...(base ?? {}) };
  for (const key of THEME_KEYS) {
    const value = override?.[key];
    if (value) result[key] = value;
  }
  return result;
}

function findSelectedPath(
  root: ProjectNodeTree | null,
  selected: AnyNodeTree | null
): AnyNodeTree[] {
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

// --- Main hook: Pure derived state ---

export function useResolvedTheme() {
  // 1. Select only what's needed (Zustand selector pattern)
  const projectData = useProjectStore((s) => s.projectData);
  const selectedNode = useProjectStore((s) => s.selectedNode);

  // 2. Derive the path (memoized for DFS performance)
  // With React Compiler, this useMemo becomes optional
  const selectedPath = useMemo(
    () => findSelectedPath(projectData, selectedNode),
    [projectData, selectedNode]
  );

  // 3. Derive the theme (pure calculation, no side effects)
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
  }, [selectedNode, selectedPath, projectData]);

  // 4. Generate CSS variables (pure derived data)
  const cssVariables: React.CSSProperties = theme
    ? {
        '--navbar-color': theme.navbarColor,
        '--left-sidebar-color': theme.leftSidebarColor,
        '--right-sidebar-color': theme.rightSidebarColor,
        '--background-color': theme.backgroundColor,
        '--text-color': theme.textColor,
        '--icon-color': theme.iconColor,
        '--card-color': theme.cardColor,
      } as React.CSSProperties
    : {};

  return { theme, cssVariables };
}
```

---

## What We Removed

- ❌ `useThemeStore` - No global theme sync
- ❌ `useEffect` for syncing - Causes double-renders
- ❌ `setTheme()` calls - No pushing to store

---

## Optional: Theme Context with `use()`

If deep components need the theme object (not just CSS variables):

```typescript
// ThemeContext.tsx
import { createContext } from 'react';
import type { ThemeConfig } from '@/types/project';

export const ThemeContext = createContext<ThemeConfig | null>(null);

// Layout.tsx
import { ThemeContext } from './ThemeContext';

export default function Layout({ navbar, leftSidebar, main }) {
  const { theme, cssVariables } = useResolvedTheme();

  return (
    <ThemeContext.Provider value={theme}>
      <div style={cssVariables}>
        {/* children */}
      </div>
    </ThemeContext.Provider>
  );
}

// DeepComponent.tsx - React 19 use() API
import { use } from 'react';
import { ThemeContext } from './ThemeContext';

function DeepComponent() {
  const theme = use(ThemeContext); // React 19 - replaces useContext
  return <div style={{ color: theme?.textColor }}>...</div>;
}
```

---

## Verification

- [ ] Theme still applies when selecting nodes
- [ ] No console warnings about useEffect
- [ ] Fewer re-renders (check React DevTools)
- [ ] `useThemeStore` can be deleted if unused elsewhere

---

## Next Step

👉 [Step 2: Panel State Hook](./step-02-layout-composition.md)
