import { memo, Fragment } from "react";
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from "@/components/ui/resizable";
import { ContextPanel } from "./ContextPanel";
import { selectTabStack } from "../../../store/selectors/tabSelectors";
import useTabStore from "../../../store/useTabStore";
import { useShallow } from "zustand/react/shallow";
import type { AnyNodeTree } from "@/types/project";

interface TabContextStackProps {
    projectData: AnyNodeTree;
    filteredProjectData?: AnyNodeTree | null;
}

export const TabContextStack = memo(function TabContextStack({
    projectData,
    filteredProjectData,
}: TabContextStackProps) {
    const activeTabId = useTabStore((s) => s.activeTabId);
    const setActiveTabId = useTabStore((s) => s.setActiveTabId);
    const destroyTabBranch = useTabStore((s) => s.destroyTabBranch);
    const updateTabLayouts = useTabStore((s) => s.updateTabLayouts);
    const tabStack = useTabStore(useShallow(selectTabStack));

    const handleLayout = (sizes: number[]) => {
        const layouts = tabStack.map((tab, i) => ({
            tabId: tab.id,
            size: sizes[i],
        }));
        updateTabLayouts(layouts);
    };

    return (
        <ResizablePanelGroup
            direction="vertical"
            className="h-full"
            onLayout={handleLayout}
        >
            {tabStack.map((tab, index) => (
                <Fragment key={tab.id}>
                    {index > 0 && (
                        <ResizableHandle
                            withHandle
                            className="bg-border hover:bg-primary/20 transition-colors h-px"
                        />
                    )}
                    <ResizablePanel
                        id={tab.id}
                        order={index}
                        minSize={10}
                        defaultSize={tab.layoutSize ?? 100 / tabStack.length}
                        className="flex flex-col overflow-hidden"
                    >
                        <ContextPanel
                            tab={tab}
                            projectTree={filteredProjectData ?? projectData}
                            isActive={tab.id === activeTabId}
                            onActivate={() => setActiveTabId(tab.id)}
                            onClose={() => destroyTabBranch(tab.id)}
                        />
                    </ResizablePanel>
                </Fragment>
            ))}
        </ResizablePanelGroup>
    );
});
