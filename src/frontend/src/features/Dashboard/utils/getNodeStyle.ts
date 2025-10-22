import type { NodeType, ThemeConfig } from "@/types/project";


const getNodeStyle = (node: { node_type: NodeType, theme?: ThemeConfig, target?: { node_type: NodeType } }) => {
    // If node has theme overrides, prefer them
    const themed = node.theme || {};
    let node_type = node.node_type;
    if (node_type == "call" && node.target) {
        node_type = node.target.node_type;
    }

    const defaults = (() => {
        switch (node_type) {
            case "project":
                return {
                    backgroundColor: "#fff",
                    color: "#1C1B1F",
                    iconColor: "#6750A4",
                    cardColor: "#F3EDF7",
                    borderColor: "#E7E0EC",
                    textColor: "#1C1B1F",
                };
            case "folder":
                return {
                    backgroundColor: "#FFFBFE",
                    color: "#1C1B1F",
                    iconColor: "#625B71",
                    cardColor: "#FFFBFE",
                    textColor: "#1C1B1F",
                    borderColor: "#E7E0EC",
                };
            case "file":
                return {
                    backgroundColor: "#FFFFFF",
                    color: "#1C1B1F",
                    iconColor: "#49454F",
                    cardColor: "#FFFFFF",
                    borderColor: "#E7E0EC",
                    textColor: "#1C1B1F",
                };
            case "function":
                return {
                    backgroundColor: "#FFFFFF",
                    color: "#7D5260",
                    iconColor: "#7D5260",
                    cardColor: "#FFFFFF",
                    textColor: "#7D5260",
                    borderColor: "#F4E7ED",
                };
            case "class":
                return {
                    backgroundColor: "#FFFFFF",
                    color: "#6750A4",
                    iconColor: "#6750A4",
                    cardColor: "#FFFFFF",
                    textColor: "#6750A4",
                    borderColor: "#E9E1F6",
                };
            case "package":
                return {
                    backgroundColor: "#FEF7FF",
                    color: "#1C1B1F",
                    iconColor: "#625B71",
                    borderColor: "#E7E0EC",
                    textColor: "#1C1B1F",
                    cardColor: "#FEF7FF",
                };
            default:
                return {
                    backgroundColor: "#FFFBFE",
                    color: "#1C1B1F",
                    iconColor: "#49454F",
                    borderColor: "#E7E0EC",
                    cardColor: "#FFFBFE",
                    textColor: "#1C1B1F",
                };
        }
    })();

    return {
        cardColor: themed.cardColor || defaults.cardColor,
        backgroundColor: themed.cardColor || defaults.backgroundColor,
        color: themed.textColor || defaults.color,
        iconColor: themed.iconColor || defaults.iconColor,
        textColor: themed.textColor || defaults.textColor,
        borderColor: defaults.borderColor,
    };
};

export default getNodeStyle;