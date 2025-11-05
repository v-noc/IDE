import type { NodeType } from "../service/useProject";

const getIcons = (nodeType: NodeType): string => {
  switch (nodeType) {
    case "folder":
      return "FaFolder";
    case "virtual_folder":
      return "FaFolder";
    case "file":
      return "FaFile";
    case "project":
      return "FaThLarge";
    case "function":
      return "TbFunction";
    case "class":
      return "FaTable";
    case "package":
      return "FiPackage";
    case "group":
      return "HiMiniRectangleGroup";
    default:
      return "FaFile";
  }
};

export default getIcons;
