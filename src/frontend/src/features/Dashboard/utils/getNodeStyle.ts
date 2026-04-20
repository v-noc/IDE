import type { CallNodeTree, ContainerNodeTree } from "@/types/project";

const getNodeStyle = (node: ContainerNodeTree) => {
  // If node has theme overrides, prefer them
  const themed = node.theme_config || {};
  let node_type = node.node_type;
  if (node_type == "call" && (node as CallNodeTree).target) {
    node_type = (node as CallNodeTree).target?.node_type || "function";
  }

  /** Theme tokens — follow `index.css` for both light and dark */
  const defaults = (() => {
    switch (node_type) {
      case "project":
        return {
          backgroundColor: "var(--muted)",
          color: "var(--foreground)",
          iconColor: "var(--primary)",
          cardColor: "var(--muted)",
          borderColor: "var(--border)",
          textColor: "var(--foreground)",
        };
      case "folder":
        return {
          backgroundColor: "var(--secondary)",
          color: "var(--foreground)",
          iconColor: "var(--muted-foreground)",
          cardColor: "var(--secondary)",
          textColor: "var(--foreground)",
          borderColor: "var(--border)",
        };
      case "file":
        return {
          backgroundColor: "var(--secondary)",
          color: "var(--foreground)",
          iconColor: "var(--muted-foreground)",
          cardColor: "var(--secondary)",
          borderColor: "var(--border)",
          textColor: "var(--foreground)",
        };
      case "function":
        return {
          backgroundColor: "var(--secondary)",
          color: "var(--foreground)",
          iconColor: "var(--primary)",
          cardColor: "var(--secondary)",
          textColor: "var(--foreground)",
          borderColor: "var(--border)",
        };
      case "class":
        return {
          backgroundColor: "var(--secondary)",
          color: "var(--foreground)",
          iconColor: "var(--primary)",
          cardColor: "var(--secondary)",
          textColor: "var(--foreground)",
          borderColor: "var(--border)",
        };

      default:
        return {
          backgroundColor: "var(--secondary)",
          color: "var(--foreground)",
          iconColor: "var(--muted-foreground)",
          borderColor: "var(--border)",
          cardColor: "var(--secondary)",
          textColor: "var(--foreground)",
        };
    }
  })();

  return {
    cardColor: themed.cardColor || defaults.cardColor,
    backgroundColor: themed.backgroundColor || defaults.backgroundColor,
    color: themed.textColor || defaults.color,
    iconColor: themed.iconColor || defaults.iconColor,
    textColor: themed.textColor || defaults.textColor,
    borderColor: defaults.borderColor,
  };
};

export default getNodeStyle;
