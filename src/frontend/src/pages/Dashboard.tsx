import Layout from "@/features/Dashboard/components/Layout";
import SideBar from "@/features/Dashboard/features/Sidebar/components/SideBar";
import Navbar from "@/features/Dashboard/features/Navbar/componets/Navbar";
import MainCanvas from "@/features/Dashboard/features/Main";

import { ResizablePanelGroup } from "@/components/ui/resizable";
import MainWithRightSidebar from "@/features/Dashboard/features/Main/MainWithRightSidebar";
import {
  ConfigSidebarContent,
  RightSidebar,
} from "@/features/Dashboard/features/Main/components/sidebar";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import getIcons from "@/features/Dashboard/utils/getIcons";

import { useMemo, useCallback } from "react";

import type { BasicInfoData } from "@/features/Dashboard/features/Main/components/sidebar/hooks/useConfigSidebarForm";

import type { CustomizationData } from "@/features/Dashboard/features/Main/components/sidebar/hooks/useConfigSidebarForm";
import type { AnyNodeTree, ThemeConfig } from "@/types/project";

function findNodeByKey(
  root: AnyNodeTree | null,
  project_key?: string | null
): AnyNodeTree | null {
  if (!root || !project_key) return null;
  const stack: AnyNodeTree[] = [root];
  while (stack.length) {
    const current = stack.pop()!;

    if (current._key === project_key) return current;
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
    () => findNodeByKey(projectData, selectedNode?._key),
    [projectData, selectedNode]
  );

  // const updateIconMutation = useUpdateNodeIcon(projectData?.id);
  // const updateNodeBasicInfoMutation = useUpdateNodeBasicInfo(projectData?.id);
  // const updateNodeThemeMutation = useUpdateNodeTheme(projectData?.id);

  const onChangeTheme = useCallback(
    (data: CustomizationData) => {
      if (!selectedNode) return;
      // const theme: ThemeConfig = {
      //   iconColor: data.iconColor,
      //   cardColor: data.cardColor,
      //   navbarColor: data.navbarColor,
      //   leftSidebarColor: data.leftSidebarColor,
      //   rightSidebarColor: data.rightSidebarColor,
      //   backgroundColor: data.backgroundColor,
      //   textColor: data.textColor,
      // };
      // updateNodeThemeMutation.mutate({
      //   elementId: selectedNode.id,
      //   theme,
      // });
    },
    [selectedNode, selectedNodeFromTree]
  );

  const onChangeBasicInfo = useCallback(
    (data: BasicInfoData) => {
      if (!selectedNode) return;
      const nextIcon =
        data.icon || getIcons(selectedNodeFromTree?.node_type ?? "project");

      if (
        selectedNodeFromTree?._key &&
        nextIcon !== selectedNodeFromTree.icon
      ) {
        // updateIconMutation.mutate({
        //   elementId: selectedNodeFromTree.id,
        //   icon: nextIcon,
        // });
      }

      if (
        selectedNodeFromTree?.name !== data.name ||
        (selectedNodeFromTree?.description ?? "") !== (data.description ?? "")
      ) {
        // updateNodeBasicInfoMutation.mutate({
        //   elementId: selectedNodeFromTree?.id ?? "",
        //   basicInfo: {
        //     name: data.name,
        //     description: data.description,
        //   },
        // });
      }
    },
    [selectedNode, selectedNodeFromTree]
  );

  const sidebarProps = useMemo(() => {
    return {
      initialBasicInfo: {
        name: selectedNodeFromTree?.name ?? "",
        description: selectedNodeFromTree?.description ?? "",
        icon: selectedNodeFromTree
          ? selectedNodeFromTree.icon ||
            getIcons(selectedNodeFromTree.node_type ?? "project")
          : getIcons("project"),
      },
      initialCustomization: {
        iconColor: selectedNodeFromTree?.theme_config?.iconColor,

        cardColor: selectedNodeFromTree?.theme_config?.cardColor,
        navbarColor: selectedNodeFromTree?.theme_config?.navbarColor,
        backgroundColor: selectedNodeFromTree?.theme_config?.backgroundColor,
        leftSidebarColor: selectedNodeFromTree?.theme_config?.leftSidebarColor,
        rightSidebarColor:
          selectedNodeFromTree?.theme_config?.rightSidebarColor,
        textColor: selectedNodeFromTree?.theme_config?.textColor,
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
            left={<></>}
            right={
              // <RightSidebar>
              <ConfigSidebarContent
                key={selectedNodeFromTree?._key}
                {...sidebarProps}
              />
              // </RightSidebar>
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
