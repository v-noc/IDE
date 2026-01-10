import { useSidebarModalStore } from "@/features/Dashboard/store/useSidebarModalStore";
import CreateGroupsDialog from "../../../components/CreateGroupsDialog";
import AddCallDialog from "./SelectNodeDialog";
import PromptBuilderDialog from "@/components/PromptBuilder/PromptBuilder";
import ManageGroupDialog from "@/features/Dashboard/components/ManageGroupsDialog";

export function SidebarDialogs() {
  const { activeModal, targetNode, closeModal } = useSidebarModalStore();

  // No node = no dialogs
  if (!targetNode) return null;

  return (
    <>
      <CreateGroupsDialog
        open={activeModal === "create-group"}
        onOpenChange={(open) => !open && closeModal()}
        node={targetNode}
      />

      <AddCallDialog
        open={activeModal === "add-call"}
        onOpenChange={(open) => !open && closeModal()}
        node={targetNode}
      />

      <PromptBuilderDialog
        open={activeModal === "prompt-builder"}
        onOpenChange={(open) => !open && closeModal()}
        node={targetNode}
      />

      <ManageGroupDialog
        open={activeModal === "manage-group"}
        onOpenChange={(open) => !open && closeModal()}
        node={targetNode}
      />
    </>
  );
}
