import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useMemo, useState } from "react";
import type {
  AnyNodeTree,
  ClassNodeTree,
  ContainerNodeTree,
  FunctionNodeTree,
} from "@/types/project";
import { TreeNode } from "../../../Sidebar/components/TreeNode";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

type NodeWithChildren = { children?: AnyNodeTree[] };

const findNodeByQName = (
  root: AnyNodeTree | null,
  qname?: string | null
): AnyNodeTree | null => {
  if (!root || !qname) return null;
  const stack: AnyNodeTree[] = [root];
  while (stack.length) {
    const current = stack.pop() as AnyNodeTree;
    if (current.qname === qname) return current;
    const children = (current as unknown as NodeWithChildren).children ?? [];
    if (children.length) {
      for (let i = children.length - 1; i >= 0; i--) {
        stack.push(children[i]);
      }
    }
  }
  return null;
};

const BaseClass = () => {
  const { selectedNode, projectData, setSecondarySelectedNode } =
    useProjectStore();
  const [showMethods, setShowMethods] = useState(false);

  const baseClassNodes = useMemo(() => {
    if (!projectData || !selectedNode || selectedNode.node_type !== "class") {
      return [] as AnyNodeTree[];
    }
    const classNode = selectedNode as ClassNodeTree;
    const baseQNames = classNode.implements || [];
    const resolved: AnyNodeTree[] = [];

    for (const q of baseQNames) {
      if (q === selectedNode.qname) continue;
      const node = findNodeByQName(projectData, q);
      if (node) resolved.push(node);
    }
    return resolved;
  }, [projectData, selectedNode]);

  const mergedMethods = useMemo(() => {
    if (!baseClassNodes.length) return [] as FunctionNodeTree[];
    const seen = new Set<string>();
    const methods: FunctionNodeTree[] = [];
    for (const cls of baseClassNodes) {
      const children = (cls as unknown as NodeWithChildren).children ?? [];
      for (const child of children) {
        if (child.node_type === "function") {
          const methodName = child.name;
          if (!seen.has(methodName)) {
            const newChild = { ...child, name: `(${cls.name}).${methodName}` };
            seen.add(methodName);
            methods.push(newChild as FunctionNodeTree);
          }
        }
      }
    }
    return methods;
  }, [baseClassNodes]);

  if (!selectedNode || selectedNode.node_type !== "class") {
    return (
      <div className="text-xs text-muted-foreground px-2 py-2">
        Select a class node to view its base classes or methods.
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="px-3 py-2 border-b bg-muted/40 flex items-center justify-between">
        <h3 className="text-xs font-semibold tracking-wide text-muted-foreground">
          Base Class Inspector
        </h3>
        <div className="flex items-center gap-2">
          <Label htmlFor="toggle-mro" className="text-xs text-muted-foreground">
            Methods (MRO)
          </Label>
          <Switch
            id="toggle-mro"
            checked={showMethods}
            onCheckedChange={setShowMethods}
          />
        </div>
      </div>

      {showMethods ? (
        <div className="flex-1 min-h-0 overflow-auto px-2 py-2 space-y-2">
          <div className="text-[11px] text-muted-foreground">
            MRO: {baseClassNodes.map((c) => c.name).join(" → ") || "N/A"}
          </div>
          {mergedMethods.length === 0 ? (
            <div className="text-xs text-muted-foreground px-1 py-2">
              No methods found across the MRO.
            </div>
          ) : (
            mergedMethods.map((method) => (
              <TreeNode
                key={method._key}
                node={method}
                onSelect={(n) => setSecondarySelectedNode(n as AnyNodeTree)}
              />
            ))
          )}
        </div>
      ) : (
        <div className="flex-1 min-h-0 overflow-auto px-2 py-2 space-y-1">
          {baseClassNodes.length === 0 ? (
            <div className="text-xs text-muted-foreground px-1 py-2">
              No base classes found for the selected class.
            </div>
          ) : (
            baseClassNodes.map((node) => (
              <TreeNode
                key={node._key}
                node={node as ContainerNodeTree}
                onSelect={(n) => setSecondarySelectedNode(n as AnyNodeTree)}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default BaseClass;
