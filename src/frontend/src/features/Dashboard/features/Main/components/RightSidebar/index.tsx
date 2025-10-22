import React, { useCallback, useMemo } from "react";
import { ChevronRight } from "lucide-react";
import CallSidebar from "./CallSidebar";
import {
  ResizableHandle,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Panel as ResizablePanel } from "react-resizable-panels";
import BaseClass from "./BaseClass";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ConfigSidebarContent from "./components/SidebarTabs";
import { getIcons } from "@/features/Dashboard/utils";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type {
  AnyNodeTree,
  ProjectNodeTree,
  ThemeConfig,
} from "@/types/project";
type NodeWithChildren = AnyNodeTree & { children?: AnyNodeTree[] };
type NodeWithTheme = AnyNodeTree & { theme_config?: ThemeConfig };
import type {
  BasicInfoData,
  CustomizationData,
} from "./hooks/useConfigSidebarForm";

export const RightSidebar: React.FC<{
  children?: React.ReactNode;
  className?: string;
  onToggle?: () => void;
}> = ({ className, onToggle }) => {
  const { selectedNode, projectData, setProjectData, setSelectedNode } =
    useProjectStore();

  const updateNodeInTree = useCallback(
    (
      tree: ProjectNodeTree,
      key: string,
      updater: (node: AnyNodeTree) => AnyNodeTree
    ): ProjectNodeTree => {
      const walk = (node: AnyNodeTree): AnyNodeTree => {
        if (node._key === key) {
          return updater({ ...node });
        }
        const children = (node as NodeWithChildren).children;
        if (Array.isArray(children) && children.length) {
          return {
            ...node,
            children: children.map((c) => walk(c)),
          } as AnyNodeTree;
        }
        return node;
      };

      return walk(tree) as ProjectNodeTree;
    },
    []
  );

  const onChangeTheme = useCallback(
    (data: CustomizationData) => {
      if (!selectedNode || !projectData) return;
      const theme: ThemeConfig = {
        iconColor: data.iconColor,
        cardColor: data.cardColor,
        navbarColor: data.navbarColor,
        leftSidebarColor: data.leftSidebarColor,
        rightSidebarColor: data.rightSidebarColor,
        backgroundColor: data.backgroundColor,
        textColor: data.textColor,
      };

      const updatedSelected: AnyNodeTree = {
        ...selectedNode,
        theme_config: { ...selectedNode.theme_config, ...theme },
      } as AnyNodeTree;

      const updatedTree = updateNodeInTree(
        projectData,
        selectedNode._key,
        (node) => ({
          ...node,
          theme_config: {
            ...((node as NodeWithTheme).theme_config ?? {}),
            ...theme,
          },
        })
      );

      setProjectData(updatedTree);
      setSelectedNode(updatedSelected);
    },
    [
      projectData,
      selectedNode,
      setProjectData,
      setSelectedNode,
      updateNodeInTree,
    ]
  );

  const onChangeBasicInfo = useCallback(
    (data: BasicInfoData) => {
      if (!selectedNode || !projectData) return;
      const nextIcon =
        data.icon || getIcons(selectedNode?.node_type ?? "project");

      const shouldUpdate =
        selectedNode?.name !== data.name ||
        (selectedNode?.description ?? "") !== (data.description ?? "") ||
        (selectedNode.icon ?? "") !== (nextIcon ?? "");

      if (!shouldUpdate) return;

      const updatedSelected: AnyNodeTree = {
        ...selectedNode,
        name: data.name,
        description: data.description ?? "",
        icon: nextIcon,
      } as AnyNodeTree;

      const updatedTree = updateNodeInTree(
        projectData,
        selectedNode._key,
        (node) => ({
          ...node,
          name: data.name,
          description: data.description ?? "",
          icon: nextIcon,
        })
      );

      setProjectData(updatedTree);
      setSelectedNode(updatedSelected);
    },
    [
      projectData,
      selectedNode,
      setProjectData,
      setSelectedNode,
      updateNodeInTree,
    ]
  );

  const sidebarProps = useMemo(() => {
    return {
      initialBasicInfo: {
        name: selectedNode?.name ?? "",
        description: selectedNode?.description ?? "",
        icon: selectedNode
          ? selectedNode.icon || getIcons(selectedNode.node_type ?? "project")
          : getIcons("project"),
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
    };
  }, [selectedNode, onChangeBasicInfo, onChangeTheme]);

  return (
    <aside
      className={`relative h-full w-full bg-[var(--right-sidebar-color)] border-l shadow-sm flex flex-col ${
        className ?? ""
      }`}
    >
      {onToggle ? (
        <button
          onClick={onToggle}
          aria-label="Hide right sidebar"
          title="Hide right sidebar"
          className="absolute group-hover:flex hidden  -left-3 top-1/2 z-20 -translate-y-1/2 rounded-md border bg-background/80 p-1 py-2 shadow hover:bg-accent"
        >
          <ChevronRight className="size-4" />
        </button>
      ) : null}

      <ResizablePanelGroup direction="vertical" className="h-full min-h-0">
        <ResizablePanel collapsible defaultSize={65} minSize={35}>
          <div className="h-full min-h-0 overflow-auto">
            <ConfigSidebarContent {...sidebarProps} />
          </div>
        </ResizablePanel>
        <ResizableHandle className="h-px bg-border shrink-0 " />
        <ResizablePanel collapsible defaultSize={35} minSize={20}>
          <div className="h-full min-h-0 flex flex-col ">
            <Tabs defaultValue="calls" className="flex-1 min-h-0 flex flex-col">
              <TabsList className="w-full p-0 bg-[var(--right-sidebar-color)]">
                <TabsTrigger
                  className="rounded-none data-[state=active]:border-none shadow-sm data-[state=active]:shadow-none data-[state=active]:bg-transparent bg-white"
                  value="calls"
                >
                  Calls
                </TabsTrigger>
                <TabsTrigger
                  className="rounded-none data-[state=active]:border-none shadow-sm data-[state=active]:shadow-none data-[state=active]:bg-transparent bg-white"
                  value="base"
                >
                  Base Class
                </TabsTrigger>
              </TabsList>
              <TabsContent value="calls" className="flex-1 min-h-0">
                <CallSidebar hideHeader />
              </TabsContent>
              <TabsContent
                value="base"
                className="flex-1 min-h-0 overflow-auto px-3 py-2"
              >
                <BaseClass />
              </TabsContent>
            </Tabs>
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </aside>
  );
};

export { default as ConfigSidebarContent } from "./components/SidebarTabs";
