import CustomTooltip from "@/components/Custom/CustomTooltip";
import CreateFolderStructureDialog from "./CreateFolderStructureDialog";

const CreateFolderStructure = () => {
  return (
    <CustomTooltip content="Create New Folder Structure">
      <CreateFolderStructureDialog />
    </CustomTooltip>
  );
};

export default CreateFolderStructure;
