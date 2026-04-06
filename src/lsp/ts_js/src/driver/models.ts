/**
 * JSON shapes returned to the backend — aligned with `vnoc_lsp_python.models`.
 */
import type { CallFrameStackWire } from "./call_resolver/frame";

export type NodePosition = {
  line: number;
  column: number;
  end_line: number;
  end_column: number;
};

export type BaseNodeJson = {
  id?: string | null;
  name: string;
  type: "class" | "function" | "call";
  position: NodePosition;
  children: BaseNodeJson[];
};

export type CallNodeJson = BaseNodeJson & {
  type: "call";
  call_index: number;
  call_col_pos: number;
};

export type FunctionNodeJson = BaseNodeJson & {
  type: "function";
};

export type ClassNodeJson = BaseNodeJson & {
  type: "class";
  base_classes: string[];
};

export type ParseFileResult = {
  nodes: BaseNodeJson[];
  content: string;
  modified: boolean;
};

export type InitializeResult = {
  status: "ok";
  extensions: string[];
};

/** `resolve_calls` RPC — mirrors Python `CallFrameStack.model_dump`. */
export type ResolveCallsResult = {
  call_frame_stack: CallFrameStackWire;
};
