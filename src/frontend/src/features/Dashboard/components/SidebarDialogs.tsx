import { useSidebarModalStore } from "@/features/Dashboard/store/useSidebarModalStore";
import GroupDialog from "./GroupDialog";
import SelectNodeDialog from "./SelectNodeDialog";
import PromptBuilder from "@/components/PromptBuilder/PromptBuilder";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import {
  getParentNodeWithDescendantCache,
  getSiblingsWithDescendantCache,
} from "@/features/Dashboard/utils/findNodeWithDescendantCache";
import queryKeys from "@/lib/queryKeys";
import { useQueryClient, useIsFetching } from "@tanstack/react-query";
import { useTreeNodeActions } from "../hooks/useNodeAction";
import type {
  AnyNodeTree,
  ContainerNodeTree,
  GroupNodeTree,
} from "@/types/project";
import { useMemo } from "react";
import { DemoReadOnlyDialog } from "@/components/DemoReadOnlyDialog";

export function SidebarDialogs() {
  const { activeModal, targetNode, closeModal } = useSidebarModalStore();
  const projectData = useProjectStore((s) => s.projectData);
  const queryClient = useQueryClient();
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);
  const projectKey = projectData?.id ?? "";

  const descendantsFetchCount = useIsFetching({
    predicate: (q) => {
      const k = q.queryKey as readonly unknown[];
      return (
        !!projectKey &&
        k.length >= 3 &&
        k[0] === queryKeys.code.all[0] &&
        k[1] === "descendants" &&
        k[2] === projectKey
      );
    },
  });

  const { handleAddCall } = useTreeNodeActions(targetNode as ContainerNodeTree);

  const { parentNode, siblings } = useMemo(() => {
    if (!targetNode || !projectData) {
      return { parentNode: null, siblings: [] as AnyNodeTree[] };
    }
    const root = projectData as ContainerNodeTree;
    const parent = getParentNodeWithDescendantCache(
      targetNode,
      root,
      queryClient,
      projectKey,
      branch,
      ref,
      compareTo,
    );
    const sibs = getSiblingsWithDescendantCache(
      targetNode,
      root,
      queryClient,
      projectKey,
      branch,
      ref,
      compareTo,
    );
    return { parentNode: parent, siblings: sibs };
  }, [
    targetNode,
    projectData,
    projectKey,
    branch,
    ref,
    compareTo,
    queryClient,
    descendantsFetchCount,
  ]);

  const readOnlyOpen = activeModal === "demo-read-only";

  // Node-targeted dialogs require a selection; read-only dialog can open from API guard without a node.
  if (!targetNode && !readOnlyOpen) return null;

  return (
    <>
      {targetNode ? (
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
            parent_node_id={parentNode?.id ?? ""}
          />

          <PromptBuilder
            open={activeModal === "prompt-builder"}
            onOpenChange={(open) => !open && closeModal()}
            rootNode={targetNode as ContainerNodeTree}
          />
        </>
      ) : null}

      <DemoReadOnlyDialog isOpen={readOnlyOpen} onClose={closeModal} />
    </>
  );
}
