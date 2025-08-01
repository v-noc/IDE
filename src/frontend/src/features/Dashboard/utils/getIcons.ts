import type { NodeType } from "../service/useProject";

const getIcons = (nodeType: NodeType) => {
  switch (nodeType) {
    case "folder":
      return "Folder";
    case "file":
      return "File";
    case "project":
      return "FolderRoot";
    case "function":
      return "Function";
    case "class":
      return "Table";
    case "package":
      return "Package";
  }
};

export default getIcons;
