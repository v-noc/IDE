import type { NodeTypes } from "@xyflow/react";
import { FunctionNode, ClassNode } from "../nodes";
import CodeNode from "../nodes/CodeNode";
import DocNode from "../nodes/DocNode";

export const nodeTypes: NodeTypes = {
    codeNode: CodeNode,
    docNode: DocNode,
    functionNode: FunctionNode,
    classNode: ClassNode,
};


