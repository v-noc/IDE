import type { CallNodeTree, ContainerNodeTree } from "@/types/project";

/** Legacy light-theme values saved on nodes — map to CSS tokens in the dark IDE. */
const LEGACY_LIGHT_COLORS = new Set([
  "white",
  "#fff",
  "#ffffff",
  "#f9f9f9",
  "#fafafa",
  "#f5f5f5",
]);

function normalizeThemeColor(value?: string | null): string | undefined {
  if (!value) return undefined;
  const trimmed = value.trim().toLowerCase();
  if (LEGACY_LIGHT_COLORS.has(trimmed)) return undefined;
  return value;
}

const getNodeStyle = (node: ContainerNodeTree) => {
  const themed = node.theme_config || {};
  let node_type = node.node_type;
  if (node_type == "call" && (node as CallNodeTree).target) {
    node_type = (node as CallNodeTree).target?.node_type || "function";
  }

  /** Theme tokens — follow `index.css` */
  const defaults = (() => {
    const card = "var(--card)";
    const panel = "var(--secondary)";
    const shared = {
      color: "var(--foreground)",
      iconColor: "var(--primary)",
      textColor: "var(--foreground)",
      borderColor: "var(--border)",
    };

    switch (node_type) {
      case "project":
        return {
          backgroundColor: "var(--muted)",
          cardColor: "var(--muted)",
          iconColor: "var(--primary)",
          ...shared,
        };
      case "folder":
      case "file":
        return {
          backgroundColor: panel,
          cardColor: card,
          iconColor: "var(--muted-foreground)",
          ...shared,
        };
      case "function":
      case "class":
        return {
          backgroundColor: panel,
          cardColor: card,
          ...shared,
        };
      default:
        return {
          backgroundColor: panel,
          cardColor: card,
          iconColor: "var(--muted-foreground)",
          ...shared,
        };
    }
  })();

  return {
    cardColor: normalizeThemeColor(themed.cardColor) || defaults.cardColor,
    backgroundColor:
      normalizeThemeColor(themed.backgroundColor) || defaults.backgroundColor,
    color: normalizeThemeColor(themed.textColor) || defaults.color,
    iconColor: normalizeThemeColor(themed.iconColor) || defaults.iconColor,
    textColor: normalizeThemeColor(themed.textColor) || defaults.textColor,
    borderColor: defaults.borderColor,
  };
};

export default getNodeStyle;
