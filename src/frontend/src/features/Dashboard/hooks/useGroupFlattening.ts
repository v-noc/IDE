import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import useProjectStore from '../store/useProjectStore';
import { containsGroup, flattenGroups } from '../utils/treeUtils';
import type { ProjectNodeTree } from '@/types/project';

/**
 * Hook to automatically flatten groups in the project tree 
 * if '?disable=group' is present in the URL.
 */
export function useGroupFlattening() {
  const [searchParams] = useSearchParams();
  const { projectData, setProjectData } = useProjectStore();

  useEffect(() => {
    if (!projectData) return;

    const disable = searchParams.get('disable');
    const disableGroup = disable?.split(',').includes('group');

    if (!disableGroup || !containsGroup(projectData)) return;

    const flattened = flattenGroups(projectData);
    const newRoot = flattened[0] as ProjectNodeTree;
    console.log("newRoot", newRoot);
    if (newRoot?.node_type === 'project') {
      setProjectData(newRoot);
    }
  }, [projectData, searchParams, setProjectData]);
}
