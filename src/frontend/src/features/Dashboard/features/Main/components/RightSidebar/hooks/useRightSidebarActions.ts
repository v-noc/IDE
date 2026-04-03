import { useCallback } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import useTabStore from '@/features/Dashboard/store/useTabStore';
import { useUpdateBasicInfo, useUpdateTheme } from '@/features/Dashboard/features/Main/service/useContainer';
import type { AnyNodeTree, ProjectNodeTree, ThemeConfig } from '@/types/project';

type NodeWithChildren = AnyNodeTree & { children?: AnyNodeTree[] };

/**
 * Update a node in the tree immutably.
 * Strictly extracted from RightSidebar layout logic.
 */
function updateNodeInTree(
  tree: ProjectNodeTree,
  key: string,
  updater: (node: AnyNodeTree) => AnyNodeTree
): ProjectNodeTree {
  const walk = (node: AnyNodeTree): AnyNodeTree => {
    if (node.id === key) {
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
}

/**
 * Mutation actions for the Right Sidebar.
 * Handles the logic of updating the project tree and selection.
 */
export function useRightSidebarActions() {
  const activeTabId = useTabStore((s) => s.activeTabId);
  const selectedNode = useProjectStore((s) => s.selectedNode[activeTabId]);
  const projectData = useProjectStore((s) => s.projectData);
  const setProjectData = useProjectStore((s) => s.setProjectData);
  const setSelectedNode = useProjectStore((s) => s.setSelectedNode);

  const { mutate: updateBasicInfoApi } = useUpdateBasicInfo(selectedNode?.id ?? '', projectData?.id ?? '');
  const { mutate: updateThemeApi } = useUpdateTheme(selectedNode?.id ?? '', projectData?.id ?? '');

  const updateTheme = useCallback((theme: ThemeConfig) => {
    if (!selectedNode || !projectData) return;

    const updatedSelected: AnyNodeTree = {
      ...selectedNode,
      theme_config: theme,
    } as AnyNodeTree;

    const updatedTree = updateNodeInTree(
      projectData,
      selectedNode.id,
      (node) => ({
        ...node,
        theme_config: theme,
      })
    );

    updateThemeApi(theme);
    setProjectData(updatedTree);
    setSelectedNode(activeTabId, updatedSelected);
  }, [projectData, selectedNode, setProjectData, setSelectedNode, activeTabId, updateThemeApi]);

  const updateBasicInfo = useCallback((info: { name: string; description: string; icon: string }) => {
    if (!selectedNode || !projectData) return;

    const updatedSelected: AnyNodeTree = {
      ...selectedNode,
      ...info,
    } as AnyNodeTree;

    const updatedTree = updateNodeInTree(
      projectData,
      selectedNode.id,
      (node) => ({
        ...node,
        ...info,
      })
    );

    updateBasicInfoApi(info);
    setProjectData(updatedTree);
    setSelectedNode(activeTabId, updatedSelected);
  }, [projectData, selectedNode, setProjectData, setSelectedNode, updateBasicInfoApi]);

  return {
    updateTheme,
    updateBasicInfo,
  };
}
