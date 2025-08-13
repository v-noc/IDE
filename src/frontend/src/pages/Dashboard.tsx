import Layout from "@/features/Dashboard/components/Layout";
import SideBar from "@/features/Dashboard/features/Sidebar/components/SideBar";
import Navbar from "@/features/Dashboard/features/Navbar/componets/Navbar";
import MainCanvas from "@/features/Dashboard/features/Main";

import { ResizablePanelGroup } from "@/components/ui/resizable";
import MainWithRightSidebar from "@/features/Dashboard/features/Main/MainWithRightSidebar";
import { RightSidebar } from "@/features/Dashboard/features/Main/components/sidebar";
import ConfigSidebarContent from "@/features/Dashboard/features/Main/components/sidebar/components/SidebarTabs";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import getIcons from "@/features/Dashboard/utils/getIcons";
import {
  useUpdateNodeIcon,
  useUpdateNodeTheme,
  useUpdateNodeBasicInfo,
} from "@/features/Dashboard/service/useNode";
import { useMemo, useCallback } from "react";
import type {
  ProjectTreeResponse,
  NodeType,
} from "@/features/Dashboard/service/useProject";
import type { BasicInfoData } from "@/features/Dashboard/features/Main/components/sidebar/hooks/useConfigSidebarForm";
import type { ThemeConfig } from "@/features/Dashboard/store/useThemeStore";
import type { CustomizationData } from "@/features/Dashboard/features/Main/components/sidebar/hooks/useConfigSidebarForm";

function findNodeByKey(
  root: ProjectTreeResponse | null,
  project_key?: string | null
): ProjectTreeResponse | null {
  if (!root || !project_key) return null;
  const stack: ProjectTreeResponse[] = [root];
  while (stack.length) {
    const current = stack.pop()!;

    if (current.id === project_key) return current;
    if (current.children && current.children.length) {
      for (let i = 0; i < current.children.length; i++) {
        stack.push(current.children[i]);
      }
    }
  }
  return null;
}

const Dashboard = () => {
  const { selectedNode, projectData } = useProjectStore();

  const selectedNodeFromTree = useMemo(
    () => findNodeByKey(projectData, selectedNode?.id),
    [projectData, selectedNode]
  );

  const updateIconMutation = useUpdateNodeIcon(projectData?.id);
  const updateNodeBasicInfoMutation = useUpdateNodeBasicInfo(projectData?.id);
  const updateNodeThemeMutation = useUpdateNodeTheme(projectData?.id);

  const onChangeTheme = useCallback(
    (data: CustomizationData) => {
      if (!selectedNode) return;
      const theme: ThemeConfig = {
        iconColor: data.iconColor,
        cardColor: data.cardColor,
        navbarColor: data.navbarColor,
        leftSidebarColor: data.leftSidebarColor,
        rightSidebarColor: data.rightSidebarColor,
        backgroundColor: data.backgroundColor,
        textColor: data.textColor,
      };
      updateNodeThemeMutation.mutate({
        elementId: selectedNode.id,
        theme,
      });
    },
    [selectedNode, updateNodeThemeMutation, selectedNodeFromTree]
  );

  const onChangeBasicInfo = useCallback(
    (data: BasicInfoData) => {
      if (!selectedNode) return;
      const nextIcon =
        data.icon ||
        getIcons((selectedNodeFromTree?.node_type ?? "project") as NodeType);

      if (selectedNodeFromTree?.id && nextIcon !== selectedNodeFromTree.icon) {
        updateIconMutation.mutate({
          elementId: selectedNodeFromTree.id,
          icon: nextIcon,
        });
      }

      if (
        selectedNodeFromTree?.name !== data.name ||
        (selectedNodeFromTree?.description ?? "") !== (data.description ?? "")
      ) {
        updateNodeBasicInfoMutation.mutate({
          elementId: selectedNodeFromTree?.id ?? "",
          basicInfo: {
            name: data.name,
            description: data.description,
          },
        });
      }
    },
    [
      selectedNode,
      updateIconMutation,
      updateNodeBasicInfoMutation,
      selectedNodeFromTree,
    ]
  );

  const sidebarProps = useMemo(() => {
    return {
      initialBasicInfo: {
        name: selectedNodeFromTree?.name ?? "",
        description: selectedNodeFromTree?.description ?? "",
        icon: selectedNodeFromTree
          ? selectedNodeFromTree.icon ||
            getIcons((selectedNodeFromTree.node_type ?? "project") as NodeType)
          : getIcons("project"),
      },
      initialCustomization: {
        iconColor: selectedNodeFromTree?.theme?.iconColor,

        cardColor: selectedNodeFromTree?.theme?.cardColor,
        navbarColor: selectedNodeFromTree?.theme?.navbarColor,
        backgroundColor: selectedNodeFromTree?.theme?.backgroundColor,
        leftSidebarColor: selectedNodeFromTree?.theme?.leftSidebarColor,
        rightSidebarColor: selectedNodeFromTree?.theme?.rightSidebarColor,
        textColor: selectedNodeFromTree?.theme?.textColor,
      },
      onChangeBasicInfo,
      onChangeCustomization: onChangeTheme,
    };
  }, [selectedNodeFromTree, onChangeBasicInfo, onChangeTheme]);

  return (
    <ResizablePanelGroup direction="horizontal">
      <Layout
        main={
          <MainWithRightSidebar
            left={<MainCanvas />}
            right={
              <RightSidebar>
                <ConfigSidebarContent
                  key={selectedNodeFromTree?.id}
                  {...sidebarProps}
                />
              </RightSidebar>
            }
          />
        }
        navbar={<Navbar />}
        leftSidebar={<SideBar />}
      />
    </ResizablePanelGroup>
  );
};

export default Dashboard;
