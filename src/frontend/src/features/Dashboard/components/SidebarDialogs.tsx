import { useSidebarModalStore } from "@/features/Dashboard/store/useSidebarModalStore";
import GroupDialog from "./GroupDialog";
import SelectNodeDialog from "./SelectNodeDialog";
import PromptBuilder from "@/components/PromptBuilder/PromptBuilder";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import {
  getParentNode,
  getSiblings,
} from "@/features/Dashboard/utils/treeUtils";
import { useTreeNodeActions } from "../hooks/useNodeAction";
import type {
  AnyNodeTree,
  ContainerNodeTree,
  GroupNodeTree,
} from "@/types/project";
import { useMemo } from "react";

export function SidebarDialogs() {
  const { activeModal, targetNode, closeModal } = useSidebarModalStore();
  const projectData = useProjectStore((s) => s.projectData);

  const { handleAddCall } = useTreeNodeActions(targetNode as ContainerNodeTree);

  // Memoize parent and siblings to avoid re-calculation on every render
  const { parentNode, siblings } = useMemo(() => {
    if (!targetNode || !projectData) return { parentNode: null, siblings: [] };
    const parent = getParentNode(targetNode, projectData as ContainerNodeTree);
    const sibs = getSiblings(targetNode, projectData as ContainerNodeTree);
    return { parentNode: parent, siblings: sibs };
  }, [targetNode, projectData]);

  // No node = no dialogs
  if (!targetNode) return null;

  return (
    <>
      <SelectNodeDialog
        isOpen={activeModal === "add-call"}
        onClose={closeModal}
        list={(projectData?.children as AnyNodeTree[]) ?? []}
        selectNodeType={["function"]}
        onSelect={(node) => {
          handleAddCall(node);
          closeModal();
        }}
      />

      <GroupDialog
        isOpen={activeModal === "create-group"}
        onClose={closeModal}
        mode="create"
        initialChildren={[targetNode as AnyNodeTree]}
        project_key={projectData?.id ?? ""}
        parent_node_id={parentNode?.id ?? ""}
        siblings={siblings}
      />

      <GroupDialog
        isOpen={activeModal === "manage-group"}
        onClose={closeModal}
        mode="manage"
        group={targetNode as unknown as GroupNodeTree}
        siblings={siblings}
        project_key={projectData?.id ?? ""}
      />

      <PromptBuilder
        open={activeModal === "prompt-builder"}
        onOpenChange={(open) => !open && closeModal()}
        rootNode={targetNode as ContainerNodeTree}
        projectId={projectData?.id ?? ""}
      />
    </>
  );
}
