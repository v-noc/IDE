import CustomTooltip from "@/components/Custom/CustomTooltip";
import { Button } from "@/components/ui/button";
import { PlusIcon } from "lucide-react";

const CreateFolderStructure = () => {
  return (
    <CustomTooltip content="Create New Folder Structure">
      <Button variant="ghost" size="icon" className="cursor-pointer ">
        <PlusIcon className="w-4 h-4" />
      </Button>
    </CustomTooltip>
  );
};

export default CreateFolderStructure;
