import { useRef, useState, useCallback } from "react";
import { type ImperativePanelHandle } from "react-resizable-panels";

/**
 * Hook to manage sidebar layout:
 * - Tracks collapse state for the project files panel.
 * - Provides refs and toggle handlers for imperative panel control.
 */
export function useSidebarPanels() {
    const [isProjectFilesCollapsed, setProjectFilesCollapsed] = useState(false);
    const projectFilePanelRef = useRef<ImperativePanelHandle>(null);

    const toggleProjectFiles = useCallback(() => {
        const panel = projectFilePanelRef.current;
        if (panel) {
            if (panel.isCollapsed()) {
                panel.expand();
            } else {
                panel.collapse();
            }
        }
    }, []);

    const onCollapse = useCallback(() => setProjectFilesCollapsed(true), []);
    const onExpand = useCallback(() => setProjectFilesCollapsed(false), []);

    return {
        isProjectFilesCollapsed,
        projectFilePanelRef,
        toggleProjectFiles,
        onCollapse,
        onExpand,
    };
}
