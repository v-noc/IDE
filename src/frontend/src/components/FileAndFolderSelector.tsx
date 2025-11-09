import { useRef } from "react";

import { FolderOpen } from "lucide-react";

import { Button } from "./ui/button";

interface FileAndFolderSelectorProps {
  handleFolderSelect: (
    e: React.ChangeEvent<HTMLInputElement>,
    isImport: boolean
  ) => void;
}
const FileAndFolderSelector = ({
  handleFolderSelect,
}: FileAndFolderSelectorProps) => {
  const importFolderInputRef = useRef<HTMLInputElement>(null);

  const openFolderBrowser = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    importFolderInputRef.current?.click();
  };

  return (
    <div>
      <Button
        variant="outline"
        size="icon"
        className="cursor-pointer"
        onClick={openFolderBrowser}
        type="button"
      >
        <FolderOpen className="h-4 w-4" />
      </Button>

      <input
        ref={importFolderInputRef}
        type="file"
        style={{ display: "none" }}
        onChange={(e) => handleFolderSelect(e, true)}
        {...({
          webkitdirectory: "",
          directory: "",
        } as React.InputHTMLAttributes<HTMLInputElement>)}
      />
    </div>
  );
};

export default FileAndFolderSelector;
