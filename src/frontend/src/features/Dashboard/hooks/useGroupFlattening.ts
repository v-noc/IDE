import { useEffect, useMemo } from 'react';
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
  const disableGroup = useMemo(() => {
    const disable = searchParams.get('disable');
    return disable?.split(',').includes('group') ?? false;
  }, [searchParams]);

  useEffect(() => {
    if (!projectData) return;
    if (!disableGroup || !containsGroup(projectData)) return;

    const flattened = flattenGroups(projectData);
    const newRoot = flattened[0] as ProjectNodeTree;
    if (newRoot?.node_type === 'project') {
      setProjectData(newRoot);
    }
  }, [projectData, disableGroup, setProjectData]);
}
