import type { ProjectTreeResponse } from "../service/useProject";

const getNodeStyle = (node: ProjectTreeResponse) => {
    // If node has theme overrides, prefer them
    const themed = node.theme || {};

    const defaults = (() => {
        switch (node.node_type) {
            case "project":
                return {
                    backgroundColor: "#F3EDF7",
                    color: "#1C1B1F",
                    iconColor: "#6750A4",
                    borderColor: "#E7E0EC",
                };
            case "folder":
                return {
                    backgroundColor: "#FFFBFE",
                    color: "#1C1B1F",
                    iconColor: "#625B71",
                    borderColor: "#E7E0EC",
                };
            case "file":
                return {
                    backgroundColor: "#FFFFFF",
                    color: "#1C1B1F",
                    iconColor: "#49454F",
                    borderColor: "#E7E0EC",
                };
            case "function":
                return {
                    backgroundColor: "#FFFFFF",
                    color: "#7D5260",
                    iconColor: "#7D5260",
                    borderColor: "#F4E7ED",
                };
            case "class":
                return {
                    backgroundColor: "#FFFFFF",
                    color: "#6750A4",
                    iconColor: "#6750A4",
                    borderColor: "#E9E1F6",
                };
            case "package":
                return {
                    backgroundColor: "#FEF7FF",
                    color: "#1C1B1F",
                    iconColor: "#625B71",
                    borderColor: "#E7E0EC",
                };
            default:
                return {
                    backgroundColor: "#FFFBFE",
                    color: "#1C1B1F",
                    iconColor: "#49454F",
                    borderColor: "#E7E0EC",
                };
        }
    })();

    return {
        backgroundColor: themed.cardColor || defaults.backgroundColor,
        color: themed.textColor || defaults.color,
        iconColor: themed.iconColor || defaults.iconColor,
        borderColor: defaults.borderColor,
    };
};

export default getNodeStyle;