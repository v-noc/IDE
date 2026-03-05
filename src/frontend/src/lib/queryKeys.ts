const queryKeys = {
  projects: {
    all: ['projects'] as const,
    list: () => [...queryKeys.projects.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.projects.all, 'detail', id] as const,
    tree: (id: string) => [...queryKeys.projects.all, 'tree', id] as const,
  },
  code: {
    all: ['code'] as const,
    detail: (elementId: string) => [...queryKeys.code.all, elementId] as const,
  },
  logs: {
    all: ['logs'] as const,
    tree: (functionId: string, projectId: string) => [...queryKeys.logs.all, 'tree', functionId, projectId] as const,
  },
  nodes: {
    all: ['nodes'] as const,
    detail: (nodeId: string) => [...queryKeys.nodes.all, nodeId] as const,
  },
  groups: {
    all: ['groups'] as const,
    list: (projectKey: string) => [...queryKeys.groups.all, 'list', projectKey] as const,
  },
  documents: {
    all: ['documents'] as const,
    list: (nodeKey: string, projectKey?: string) => [...queryKeys.documents.all, 'list', nodeKey, projectKey ?? ''] as const,
    detail: (docId: string) => [...queryKeys.documents.all, 'detail', docId] as const,
  },
  versioning: {
    all: ['versioning'] as const,
    branches: (projectId: string) => [...queryKeys.versioning.all, 'branches', projectId] as const,
    commits: (projectId: string, nodeId: string, start?: number, count?: number) =>
      [...queryKeys.versioning.all, 'commits', projectId, nodeId, start ?? 0, count ?? 10] as const,
    diff: (projectId: string, afterCommitId: string, beforeCommitId: string) =>
      [...queryKeys.versioning.all, 'diff', projectId, afterCommitId, beforeCommitId] as const,
  },
} as const;

export default queryKeys;
