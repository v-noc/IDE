import type { ContainerNodeTree, AnyNodeTree, NodeType } from "@/types/project";

export type PromptSelectableNode = AnyNodeTree | ContainerNodeTree;

export interface NodeSelectionState {
  checked: Record<string, boolean>; // node._key -> included in prompt
  includeDocs: Record<string, boolean>; // node._key -> include documents
  includeCode: Record<string, boolean>; // node._key -> include code (functions/classes/files/calls)
  expanded: Record<string, boolean>; // local expand state inside builder
  selectedNodeKey: string | null; // which node is focused in builder UI
}

export interface PromptBuilderInputs {
  rootNode: ContainerNodeTree;
}

export interface GeneratedPromptResult {
  xml: string;
}

export const supportsCode = (nodeType: NodeType): boolean => {
  return nodeType === "function" || nodeType === "class" || nodeType === "file" || nodeType === "call";
};


