/** Mirrors Python `CallFrameStack` (qname, id, children, dedup, cycle guard). */

export interface CallFrameNode {
  targetQName: string;
  targetId: string;
  children: CallFrameNode[];
  parent?: CallFrameNode;
  callCount: number;
}

export function createRootFrame(): CallFrameNode {
  return { targetQName: "root", targetId: "root", children: [], callCount: 1 };
}

/** Dedup by `targetQName` (same as Python `CallFrameStack.add_child`). */
export function addChild(
  parent: CallFrameNode,
  child: Omit<CallFrameNode, "parent" | "children"> & {
    children?: CallFrameNode[];
  },
): CallFrameNode {
  const full: CallFrameNode = {
    ...child,
    children: child.children ?? [],
    callCount: child.callCount ?? 1,
  };
  for (const existing of parent.children) {
    if (existing.targetQName === full.targetQName) {
      existing.callCount += 1;
      return existing;
    }
  }
  parent.children.push(full);
  full.parent = parent;
  return full;
}

export function isAncestor(
  frame: CallFrameNode | undefined,
  qualifiedName: string,
): boolean {
  let current: CallFrameNode | undefined = frame;
  while (current) {
    if (current.targetQName === qualifiedName) return true;
    current = current.parent;
  }
  return false;
}

/** Same as Python `_merge_frame_stack` (match children by `target_id`). */
export function mergeFrameStack(target: CallFrameNode, source: CallFrameNode): void {
  for (const sourceChild of source.children) {
    let matched = target.children.find((c) => c.targetId === sourceChild.targetId);
    if (!matched) {
      matched = {
        targetQName: sourceChild.targetQName,
        targetId: sourceChild.targetId,
        children: [],
        callCount: sourceChild.callCount,
        parent: target,
      };
      target.children.push(matched);
    }
    mergeFrameStack(matched, sourceChild);
  }
}

/** Wire JSON: snake_case, no `parent` (matches `model_dump` for API consumers). */
export type CallFrameStackWire = {
  target_qname: string;
  target_id: string;
  call_count: number;
  children: CallFrameStackWire[];
};

export function toCallFrameStackWire(node: CallFrameNode): CallFrameStackWire {
  return {
    target_qname: node.targetQName,
    target_id: node.targetId,
    call_count: node.callCount,
    children: node.children.map(toCallFrameStackWire),
  };
}
