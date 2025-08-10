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

    if (current.key === project_key) return current;
    if (current.children && current.children.length) {
      for (let i = 0; i < current.children.length; i++) {
        stack.push(current.children[i]);
      }
    }
  }
  return null;
}

const Dashboard = () => {
  const { selectedNodeId, projectData } = useProjectStore();

  const selectedNode = useMemo(
    () => findNodeByKey(projectData, selectedNodeId),
    [projectData, selectedNodeId]
  );

  const updateIconMutation = useUpdateNodeIcon(projectData?.key);
  const updateNodeBasicInfoMutation = useUpdateNodeBasicInfo(projectData?.key);
  const updateNodeThemeMutation = useUpdateNodeTheme(projectData?.key);

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
        elementKey: selectedNode.key,
        theme,
      });
    },
    [selectedNode, updateNodeThemeMutation]
  );

  const onChangeBasicInfo = useCallback(
    (data: BasicInfoData) => {
      if (!selectedNode) return;
      const nextIcon =
        data.icon ||
        getIcons((selectedNode.node_type ?? "project") as NodeType);

      if (selectedNode.key && nextIcon !== selectedNode.icon) {
        updateIconMutation.mutate({
          elementKey: selectedNode.key,
          icon: nextIcon,
        });
      }

      if (
        selectedNode.name !== data.name ||
        (selectedNode.description ?? "") !== (data.description ?? "")
      ) {
        updateNodeBasicInfoMutation.mutate({
          elementKey: selectedNode.key,
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
      selectedNodeId,
    ]
  );

  const sidebarProps = useMemo(() => {
    return {
      initialBasicInfo: {
        name: selectedNode?.name ?? "",
        description: selectedNode?.description ?? "",
        icon: selectedNode
          ? selectedNode.icon ||
            getIcons((selectedNode.node_type ?? "project") as NodeType)
          : getIcons("project"),
      },
      initialCustomization: {
        iconColor: selectedNode?.theme?.iconColor,

        cardColor: selectedNode?.theme?.cardColor,
        navbarColor: selectedNode?.theme?.navbarColor,
        backgroundColor: selectedNode?.theme?.backgroundColor,
        leftSidebarColor: selectedNode?.theme?.leftSidebarColor,
        rightSidebarColor: selectedNode?.theme?.rightSidebarColor,
        textColor: selectedNode?.theme?.textColor,
      },
      onChangeBasicInfo,
      onChangeCustomization: onChangeTheme,
    };
  }, [selectedNode, onChangeBasicInfo, onChangeTheme]);

  return (
    <ResizablePanelGroup direction="horizontal">
      <Layout
        main={
          <MainWithRightSidebar
            left={<MainCanvas />}
            right={
              <RightSidebar>
                <ConfigSidebarContent
                  key={selectedNode?.key}
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
