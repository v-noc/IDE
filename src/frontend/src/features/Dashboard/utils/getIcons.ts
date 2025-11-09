import type { NodeType } from "@/types/project";

const getIcons = (nodeType: NodeType): string => {
  switch (nodeType) {
    case "folder":
      return "FaFolder";

    case "file":
      return "FaFile";
    case "project":
      return "FaThLarge";
    case "function":
      return "TbFunction";
    case "class":
      return "FaTable";

    case "group":
      return "HiMiniRectangleGroup";
    default:
      return "FaFile";
  }
};

export default getIcons;
