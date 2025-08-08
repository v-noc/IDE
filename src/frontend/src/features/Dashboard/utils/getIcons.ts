import type { NodeType } from "../service/useProject";

const getIcons = (nodeType: NodeType) => {
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
    case "package":
      return "FiPackage";
  }
};

export default getIcons;
