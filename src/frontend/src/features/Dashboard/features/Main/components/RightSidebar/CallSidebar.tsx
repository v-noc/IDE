import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useMemo } from "react";
import { TreeNode } from "../../../Sidebar/components/TreeNode";
import {
  type AnyNodeTree,
  type ContainerNodeTree,
  type GroupNode,
} from "@/types/project";

type CallSidebarProps = {
  hideHeader?: boolean;
};

const CallSidebar = ({ hideHeader }: CallSidebarProps) => {
  const { focusStack, selectedNode, setSecondarySelectedNode } =
    useProjectStore();

  const callChildren = useMemo(() => {
    if (selectedNode) {
      return selectedNode.children.filter(
        (node) =>
          node.node_type == "call" ||
          (node.node_type == "group" &&
            (node as GroupNode).group_type == "call")
      );
    }
    if (focusStack.length > 0) {
      return focusStack[focusStack.length - 1].children.filter(
        (node) =>
          node.node_type == "call" ||
          (node.node_type == "group" &&
            (node as GroupNode).group_type == "call")
      );
    }

    return [];
  }, [selectedNode, focusStack]);

  return (
    <div className="h-full flex flex-col">
      {!hideHeader && (
        <div className="px-3 py-2 border-b bg-muted/40">
          <h3 className="text-xs font-semibold tracking-wide text-muted-foreground">
            Calls
          </h3>
        </div>
      )}
      <div className="flex-1 min-h-0 overflow-auto px-2 py-2 space-y-1">
        {callChildren.length === 0 ? (
          <div className="text-xs text-muted-foreground px-1 py-2">
            No calls under the selected node.
          </div>
        ) : (
          callChildren.map((call_node) => (
            <TreeNode
              key={call_node._key}
              node={call_node as ContainerNodeTree}
              childFilter={(node) =>
                node.node_type === "call" ||
                (node.node_type == "group" &&
                  (node as unknown as GroupNode).group_type == "call")
              }
              onSelect={(n) => setSecondarySelectedNode(n as AnyNodeTree)}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default CallSidebar;
