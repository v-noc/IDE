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
    const tabStack = useTabStore(useShallow(selectTabStack));

    return (
        <ResizablePanelGroup direction="vertical" className="h-full">
            {tabStack.map((tab, index) => (
                <Fragment key={tab.id}>
                    {index > 0 && (
                        <ResizableHandle
                            withHandle
                            className="bg-border hover:bg-primary/20 transition-colors h-px"
                        />
                    )}
                    <ResizablePanel
                        minSize={15}
                        defaultSize={100 / tabStack.length}
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
