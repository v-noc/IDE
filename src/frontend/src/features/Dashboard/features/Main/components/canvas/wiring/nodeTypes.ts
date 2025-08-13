import type { NodeTypes } from "@xyflow/react";
import { FunctionNode, ClassNode, MethodNode, CircleNode } from "../nodes";

export const nodeTypes: NodeTypes = {
    function: FunctionNode,
    class: ClassNode,
    method: MethodNode,
    circle: CircleNode,
};


