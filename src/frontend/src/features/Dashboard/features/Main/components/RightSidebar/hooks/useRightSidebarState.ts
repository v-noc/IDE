import { useMemo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import useTabStore from '@/features/Dashboard/store/useTabStore';
import { getIcons } from '@/features/Dashboard/utils';

/**
 * Prepares derived state for the Right Sidebar components.
 * Primarily used for initializing form data.
 */
export function useRightSidebarState() {
    const activeTabId = useTabStore((s) => s.activeTabId);
    const selectedNode = useProjectStore((s) => s.selectedNode[activeTabId]);

    return useMemo(() => {
        const initialBasicInfo = {
            name: selectedNode?.name ?? "",
            description: selectedNode?.description ?? "",
            icon: selectedNode
                ? selectedNode.icon || getIcons(selectedNode.node_type ?? "project")
                : getIcons("project"),
        };

        const initialCustomization = {
            iconColor: selectedNode?.theme_config?.iconColor,
            cardColor: selectedNode?.theme_config?.cardColor,
            navbarColor: selectedNode?.theme_config?.navbarColor,
            backgroundColor: selectedNode?.theme_config?.backgroundColor,
            leftSidebarColor: selectedNode?.theme_config?.leftSidebarColor,
            rightSidebarColor: selectedNode?.theme_config?.rightSidebarColor,
            textColor: selectedNode?.theme_config?.textColor,
        };

        return {
            initialBasicInfo,
            initialCustomization,
            hasSelection: !!selectedNode,
            nodeType: selectedNode?.node_type,
        };
    }, [selectedNode]);
}
