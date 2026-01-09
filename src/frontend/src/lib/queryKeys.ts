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
    tree: (nodeId: string) => [...queryKeys.logs.all, 'tree', nodeId] as const,
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
    list: (nodeKey: string) => [...queryKeys.documents.all, 'list', nodeKey] as const,
    detail: (docId: string) => [...queryKeys.documents.all, 'detail', docId] as const,
  },
} as const;

export default queryKeys;
