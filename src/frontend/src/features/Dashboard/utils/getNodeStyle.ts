import type { ProjectTreeResponse } from "../service/useProject";

const getNodeStyle = (node: ProjectTreeResponse) => {

    switch (node.node_type) {
        case "project":
            return {
                backgroundColor: "#F3EDF7", // surface-1 vibe
                color: "#1C1B1F", // on-surface
                iconColor: "#6750A4", // primary
                borderColor: "#E7E0EC", // surfaceVariant
            };
        case "folder":
            return {
                backgroundColor: "#FFFBFE", // surface
                color: "#1C1B1F", // on-surface
                iconColor: "#625B71", // secondary
                borderColor: "#E7E0EC", // surfaceVariant
            };
        case "file":
            return {
                backgroundColor: "#FFFFFF", // elevated surface
                color: "#1C1B1F",
                iconColor: "#49454F", // on-surface-variant
                borderColor: "#E7E0EC",
            };
        case "function":
            return {
                backgroundColor: "#FFFFFF",
                color: "#7D5260", // tertiary
                iconColor: "#7D5260",
                borderColor: "#F4E7ED", // light tertiary tint
            };
        case "class":
            return {
                backgroundColor: "#FFFFFF",
                color: "#6750A4", // primary
                iconColor: "#6750A4",
                borderColor: "#E9E1F6", // light primary tint
            };
        case "package":
            return {
                backgroundColor: "#FEF7FF", // surface-2 feel
                color: "#1C1B1F",
                iconColor: "#625B71", // secondary (keeps it distinct)
                borderColor: "#E7E0EC",
            };
        default:
            return {
                backgroundColor: "#FFFBFE", // surface
                color: "#1C1B1F",
                iconColor: "#49454F", // on-surface-variant
                borderColor: "#E7E0EC", // outline/surfaceVariant
            };
    }
}

export default getNodeStyle;