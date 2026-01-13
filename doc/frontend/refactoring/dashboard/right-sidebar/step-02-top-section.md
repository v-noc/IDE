# Step 2: Right Sidebar - Top Section (Config)

## Goal
Document the Config section structure for clarity.

---

## Structure

```
Right Sidebar Top Section
├── ConfigSidebarContent (SidebarTabs.tsx)
│   ├── BasicInfoSection      # Name, description, icon
│   ├── LogsSection          # Logs tree display
│   ├── DocumentsList        # Associated documents
│   └── CustomizationSection # Theme colors
```

---

## NEW: `RightSidebar/hooks/useSidebarProps.ts`

```typescript
import { useMemo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { getIcons } from '@/features/Dashboard/utils';
import type { BasicInfoData, CustomizationData } from './useNodeUpdates';

interface UseSidebarPropsOptions {
  onChangeBasicInfo: (data: BasicInfoData) => void;
  onChangeTheme: (data: CustomizationData) => void;
}

export function useSidebarProps({ onChangeBasicInfo, onChangeTheme }: UseSidebarPropsOptions) {
  const selectedNode = useProjectStore((s) => s.selectedNode);

  return useMemo(() => ({
    initialBasicInfo: {
      name: selectedNode?.name ?? '',
      description: selectedNode?.description ?? '',
      icon: selectedNode
        ? selectedNode.icon || getIcons(selectedNode.node_type ?? 'project')
        : getIcons('project'),
    },
    initialCustomization: {
      iconColor: selectedNode?.theme_config?.iconColor,
      cardColor: selectedNode?.theme_config?.cardColor,
      navbarColor: selectedNode?.theme_config?.navbarColor,
      backgroundColor: selectedNode?.theme_config?.backgroundColor,
      leftSidebarColor: selectedNode?.theme_config?.leftSidebarColor,
      rightSidebarColor: selectedNode?.theme_config?.rightSidebarColor,
      textColor: selectedNode?.theme_config?.textColor,
    },
    onChangeBasicInfo,
    onChangeCustomization: onChangeTheme,
  }), [selectedNode, onChangeBasicInfo, onChangeTheme]);
}
```

---

## Sections Clean Structure

Each section should follow this pattern:

```typescript
// sections/BasicInfoSection.tsx
interface BasicInfoSectionProps {
  initialData: BasicInfoData;
  onChange: (data: BasicInfoData) => void;
}

export function BasicInfoSection({ initialData, onChange }: BasicInfoSectionProps) {
  // Local form state
  // Submit handler calls onChange
}

// sections/LogsSection.tsx
interface LogsSectionProps {
  nodeId: string | undefined;
}

export function LogsSection({ nodeId }: LogsSectionProps) {
  const { data: logs } = useLogTree(nodeId); // From unified service
  return <LogsTree logs={logs ?? []} />;
}
```

---

## Verification

- [ ] Config section still renders
- [ ] Form changes still trigger updates

---

## Next Step

👉 [step-03-bottom-section.md](./step-03-bottom-section.md)
