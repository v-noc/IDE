import type { NodeTypes } from "@xyflow/react";
import { FunctionNode, ClassNode, MethodNode } from "../nodes";

export const nodeTypes: NodeTypes = {
    function: FunctionNode,
    class: ClassNode,
    method: MethodNode,
};


