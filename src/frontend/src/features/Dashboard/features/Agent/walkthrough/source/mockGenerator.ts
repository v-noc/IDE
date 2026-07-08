/**
 * Data sources:
 * - `types/project.ts` — node tree fields (children, lazy_child_ids, position, node_type, target)
 * - `service/codeDescendants` — `getCodeDescendantsQueryOptions`, `canLazyLoadCodeChildren`
 * - `utils/findNodeWithDescendantCache` — `findNodeByIdWithDescendantCache`
 * - `utils/mergeCodeTreeChildren` — `mergeStructureAndLazyChildren`
 * - `utils/resolveLineageFromPath` + `services/code/api` — lineage fallback (same as ensureOnCanvas)
 */
import type { QueryClient } from "@tanstack/react-query";
import { codeApi } from "@/services/code/api";
import {
  canLazyLoadCodeChildren,
  getCodeDescendantsQueryOptions,
} from "@/features/Dashboard/service/codeDescendants";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import { resolveLineageFromPath } from "@/features/Dashboard/utils/resolveLineageFromPath";
import { findNodeByIdWithDescendantCache } from "@/features/Dashboard/utils/findNodeWithDescendantCache";
import { mergeStructureAndLazyChildren } from "@/features/Dashboard/utils/mergeCodeTreeChildren";
import type {
  AnyNodeTree,
  CallNodeTree,
  CodePosition,
  ContainerNodeTree,
  ProjectNodeTree,
} from "@/types/project";
import type {
  Estimate,
  Frame,
  NodeSteps,
  RunRequest,
  VisitList,
  VisitNode,
  WalkthroughSession,
} from "../types";
import { visitNodeSchema } from "../types";
import { loremBlockText, loremIntro } from "./lorem";

const LINE_GATE = 8;
const VISIT_CAP = 40;
const MAX_DEPTH = 3;
const FOCUS_LABELS = ["setup", "core logic", "error handling", "result", "validation"];

type StopKind = VisitNode["node_type"];

function stopKind(nodeType: string): StopKind | null {
  if (nodeType === "group" || nodeType === "container") return null;
  if (
    nodeType === "folder" ||
    nodeType === "file" ||
    nodeType === "class" ||
    nodeType === "function" ||
    nodeType === "call" ||
    nodeType === "project"
  ) {
    return nodeType;
  }
  return null;
}

function positionOf(node: AnyNodeTree): CodePosition | undefined {
  if ("position" in node && node.position) {
    return node.position as CodePosition;
  }
  return undefined;
}

function sortChildren(nodes: AnyNodeTree[]): AnyNodeTree[] {
  return [...nodes].sort((a, b) => {
    const aLine = positionOf(a)?.line_no;
    const bLine = positionOf(b)?.line_no;
    if (aLine != null && bLine != null) return aLine - bLine;
    if (aLine != null) return -1;
    if (bLine != null) return 1;
    return a.name.localeCompare(b.name);
  });
}

async function fetchLazyChildren(
  queryClient: QueryClient,
  projectKey: string,
  node: ContainerNodeTree,
): Promise<AnyNodeTree[]> {
  const { branch, checkedOutCommitId: ref, compareToCommitId: compareTo } =
    useVersioningStore.getState();

  try {
    const data = await queryClient.fetchQuery(
      getCodeDescendantsQueryOptions(projectKey, node.id, branch, ref, compareTo),
    );
    return (data?.children ?? []) as unknown as AnyNodeTree[];
  } catch {
    return [];
  }
}

async function getEffectiveChildren(
  queryClient: QueryClient,
  projectKey: string,
  node: ContainerNodeTree,
): Promise<AnyNodeTree[]> {
  const structure = (node.children ?? []) as AnyNodeTree[];
  const lazyHint = node.lazy_child_ids?.length ?? 0;

  if (
    lazyHint > 0 &&
    canLazyLoadCodeChildren(
      node as Parameters<typeof canLazyLoadCodeChildren>[0],
    )
  ) {
    const loaded = await fetchLazyChildren(queryClient, projectKey, node);
    return mergeStructureAndLazyChildren(structure, loaded);
  }

  return structure;
}

function codeBounds(
  node: AnyNodeTree,
): { start: number | null; end: number | null; count: number | null } {
  if (node.node_type === "function" || node.node_type === "class") {
    const pos = positionOf(node);
    if (!pos) return { start: null, end: null, count: null };
    const count = Math.max(0, pos.end_line_no - pos.line_no + 1);
    return { start: pos.line_no, end: pos.end_line_no, count };
  }

  if (node.node_type === "call") {
    const call = node as CallNodeTree;
    const target = call.target;
    if (!target) return { start: null, end: null, count: null };
    const pos = target.position;
    if (!pos) return { start: null, end: null, count: null };
    const count = Math.max(0, pos.end_line_no - pos.line_no + 1);
    return { start: pos.line_no, end: pos.end_line_no, count };
  }

  return { start: null, end: null, count: null };
}

function hasCode(node: AnyNodeTree): boolean {
  if (node.node_type === "function" || node.node_type === "class") {
    return positionOf(node) != null;
  }
  if (node.node_type === "call") {
    const call = node as CallNodeTree;
    return Boolean(call.target?.position);
  }
  return false;
}

function duplicateKey(node: AnyNodeTree): string | null {
  if (node.node_type === "call") {
    return (node as CallNodeTree).target?.id ?? null;
  }
  if (node.node_type === "function" || node.node_type === "class") {
    return node.id;
  }
  return null;
}

async function resolveStartNode(
  queryClient: QueryClient,
  projectData: ProjectNodeTree,
  projectKey: string,
  startNodeId: string,
): Promise<AnyNodeTree> {
  const cached = findNodeByIdWithDescendantCache(
    queryClient,
    projectData,
    projectKey,
    startNodeId,
  );
  if (cached) return cached;

  try {
    const { path_ids } = await codeApi.getLineage(projectKey, startNodeId);
    if (path_ids?.length) {
      const lineage = await resolveLineageFromPath(
        queryClient,
        projectData,
        projectKey,
        path_ids,
      );
      if (lineage?.length) {
        return lineage[lineage.length - 1];
      }
    }
  } catch {
    // fall through
  }

  throw new Error(`Start node not found: ${startNodeId}`);
}

function estBlocks(visit: VisitNode): number {
  if (visit.mode === "contextual" || !visit.has_code) return 0;
  if (!visit.gated) return 1;
  const lines = visit.line_count ?? 0;
  return Math.max(2, Math.min(6, Math.ceil(lines / 15)));
}

export function computeMockEstimate(visitList: VisitList): Estimate {
  const nodeCount = visitList.nodes.length;
  const over_cap = Boolean(visitList.truncated) || nodeCount > VISIT_CAP;
  const step_estimate = visitList.nodes.reduce(
    (sum, node) => sum + 1 + estBlocks(node),
    0,
  );
  const llm_call_estimate =
    nodeCount +
    visitList.nodes.filter((node) => node.mode === "full" && node.gated).length +
    visitList.nodes.reduce((sum, node) => sum + estBlocks(node), 0);

  return {
    node_count: nodeCount,
    step_estimate,
    llm_call_estimate,
    over_cap,
  };
}

export async function buildMockVisitList(
  queryClient: QueryClient,
  projectData: ProjectNodeTree,
  projectKey: string,
  startNodeId: string,
  depth: number,
): Promise<VisitList> {
  const cappedDepth = Math.max(0, Math.min(depth, MAX_DEPTH));
  await resolveStartNode(queryClient, projectData, projectKey, startNodeId);

  const explained = new Map<string, number>();
  const visits: VisitNode[] = [];
  let order = 0;
  let truncated = false;
  let totalStops = 0;

  async function visit(
    node: AnyNodeTree,
    level: number,
    parentOrder: number | null,
  ): Promise<void> {
    const kind = stopKind(node.node_type);
    if (kind == null) {
      const children = await getEffectiveChildren(
        queryClient,
        projectKey,
        node as ContainerNodeTree,
      );
      for (const child of sortChildren(children)) {
        await visit(child, level, parentOrder);
      }
      return;
    }

    totalStops += 1;
    if (visits.length >= VISIT_CAP) {
      truncated = true;
      return;
    }

    const tid = duplicateKey(node);
    const firstSeen = tid != null ? explained.get(tid) : undefined;
    const mode: VisitNode["mode"] =
      tid != null && explained.has(tid) ? "contextual" : "full";

    const bounds = codeBounds(node);
    const codeAvailable = hasCode(node);
    const visitHasCode = mode === "full" && codeAvailable;
    const gated =
      mode === "full" &&
      visitHasCode &&
      bounds.count != null &&
      bounds.count >= LINE_GATE;

    const currentOrder = order;
    const visitNode = visitNodeSchema.parse({
      node_id: node.id,
      name: node.name,
      qname: node.qname ?? null,
      node_type: kind,
      description: node.description ?? "",
      level,
      order: currentOrder,
      parent_order: parentOrder,
      target_id: node.node_type === "call" ? (node as CallNodeTree).target?.id ?? null : null,
      mode,
      first_seen_order: mode === "contextual" ? (firstSeen ?? null) : null,
      has_code: mode === "contextual" ? false : visitHasCode,
      start_line: mode === "contextual" ? null : bounds.start,
      end_line: mode === "contextual" ? null : bounds.end,
      line_count: mode === "contextual" ? null : bounds.count,
      gated: mode === "contextual" ? false : gated,
    });

    visits.push(visitNode);
    order += 1;

    if (mode === "full" && tid != null) {
      explained.set(tid, currentOrder);
    }

    if (mode !== "full") {
      return;
    }

    const children = await getEffectiveChildren(
      queryClient,
      projectKey,
      node as ContainerNodeTree,
    );
    for (const child of sortChildren(children)) {
      if (level + 1 > cappedDepth) continue;
      await visit(child, level + 1, currentOrder);
    }
  }

  const startNode = await resolveStartNode(
    queryClient,
    projectData,
    projectKey,
    startNodeId,
  );
  await visit(startNode, 0, null);

  if (totalStops > VISIT_CAP) {
    truncated = true;
  }

  return {
    start_node_id: startNodeId,
    depth: cappedDepth,
    nodes: visits,
    truncated,
  };
}

function splitIntoBlocks(
  startLine: number,
  endLine: number,
  gated: boolean,
  lineCount: number,
): Array<{ start_line: number; end_line: number; focus: string }> {
  if (!gated) {
    return [{ start_line: startLine, end_line: endLine, focus: "core logic" }];
  }

  const upper = Math.max(2, Math.min(5, Math.floor(lineCount / 2)));
  const count = 2 + Math.floor(Math.random() * (upper - 2 + 1));
  const total = endLine - startLine + 1;
  const base = Math.floor(total / count);
  const remainder = total % count;

  const blocks: Array<{ start_line: number; end_line: number; focus: string }> =
    [];
  let cursor = startLine;
  for (let index = 0; index < count; index += 1) {
    const size = base + (index < remainder ? 1 : 0);
    const blockEnd = cursor + size - 1;
    blocks.push({
      start_line: cursor,
      end_line: blockEnd,
      focus: FOCUS_LABELS[index % FOCUS_LABELS.length],
    });
    cursor = blockEnd + 1;
  }
  return blocks;
}

export function generateMockFrames(
  session: WalkthroughSession,
): Array<{ delay: number; frame: Frame }> {
  const frames: Array<{ delay: number; frame: Frame }> = [
    {
      delay: 0,
      frame: {
        kind: "hello",
        protocol: 1,
        session: { ...session, node_steps: [] },
      },
    },
  ];

  let seq = 0;
  let nodeStepIndex = 0;

  for (const visit of session.visit_list.nodes) {
    const stepIndex = nodeStepIndex;
    frames.push({
      delay: 150 + Math.floor(Math.random() * 351),
      frame: {
        kind: "patch",
        seq,
        ops: [
          {
            op: "add",
            path: "/node_steps/-",
            value: {
              node_id: visit.node_id,
              order: visit.order,
              mode: visit.mode,
              intro_text: "",
              degraded: false,
              blocks: [],
            } satisfies NodeSteps,
          },
        ],
      },
    });
    seq += 1;
    nodeStepIndex += 1;

    frames.push({
      delay: 150 + Math.floor(Math.random() * 351),
      frame: {
        kind: "patch",
        seq,
        ops: [
          {
            op: "replace",
            path: `/node_steps/${stepIndex}/intro_text`,
            value: loremIntro(visit.name, visit.node_type),
          },
          {
            op: "replace",
            path: `/node_steps/${stepIndex}/degraded`,
            value: false,
          },
        ],
      },
    });
    seq += 1;

    if (visit.mode === "contextual" || !visit.has_code) {
      continue;
    }

    const blocks = splitIntoBlocks(
      visit.start_line ?? 1,
      visit.end_line ?? visit.start_line ?? 1,
      visit.gated,
      visit.line_count ?? 1,
    );

    for (let blockIndex = 0; blockIndex < blocks.length; blockIndex += 1) {
      const block = blocks[blockIndex];
      frames.push({
        delay: 150 + Math.floor(Math.random() * 351),
        frame: {
          kind: "patch",
          seq,
          ops: [
            {
              op: "add",
              path: `/node_steps/${stepIndex}/blocks/-`,
              value: {
                index: blockIndex,
                start_line: block.start_line,
                end_line: block.end_line,
                focus: block.focus,
                text: "",
                degraded: false,
              },
            },
          ],
        },
      });
      seq += 1;
    }

    blocks.forEach((block, blockIndex) => {
      frames.push({
        delay: 150 + Math.floor(Math.random() * 351),
        frame: {
          kind: "patch",
          seq,
          ops: [
            {
              op: "replace",
              path: `/node_steps/${stepIndex}/blocks/${blockIndex}/text`,
              value: loremBlockText(block.focus, blockIndex),
            },
          ],
        },
      });
      seq += 1;
    });
  }

  frames.push({
    delay: 150 + Math.floor(Math.random() * 351),
    frame: {
      kind: "patch",
      seq,
      ops: [{ op: "replace", path: "/status", value: "complete" }],
    },
  });
  seq += 1;

  frames.push({
    delay: 0,
    frame: { kind: "end", status: "complete" },
  });

  return frames;
}

export function buildMockSession(
  req: RunRequest,
  visitList: VisitList,
): WalkthroughSession {
  return {
    id: `mock-${Date.now()}`,
    created_at: new Date().toISOString(),
    request: req,
    branch: "main",
    commit_id: "mock",
    visit_list: visitList,
    node_steps: [],
    status: "generating",
    error_log: [],
    schema_version: "1",
    prompt_version: "1",
    model_id: "mock:lorem",
    usage: { prompt_tokens: 0, completion_tokens: 0 },
  };
}
