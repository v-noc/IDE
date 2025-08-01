import type { ProjectTreeResponse } from "../service/useProject";

const getNodeStyle = (node: ProjectTreeResponse) => {
    // Light Theme with Colorful Icons
    switch (node.node_type) {
        case "project":
            return {
                backgroundColor: "rgba(245, 248, 252, 0.9)", // A very light, cool grey
                color: "#1E293B", // Darker text for contrast
                iconColor: "#7B61FF", // A vibrant indigo for the main project icon
                borderColor: "rgba(226, 232, 240, 0.8)",
            }
        case "folder":
            return {
                backgroundColor: "rgba(248, 250, 252, 0.5)", // Slight variation
                color: "#334155",
                iconColor: "#FACC15", // A warm yellow for folders
                borderColor: "rgba(226, 232, 240, 0.8)",
            }
        case "file":
            return {
                backgroundColor: "rgba(248, 250, 252, 0.5)",
                color: "#334155",
                iconColor: "#64748B", // A neutral slate grey for files
                borderColor: "rgba(226, 232, 240, 0.8)",
            }
        case "function": {
            return {
                backgroundColor: "rgba(248, 250, 252, 0.5)",
                color: "#334155",
                iconColor: "#2DD4BF", // A bright teal for functions
                borderColor: "rgba(226, 232, 240, 0.8)",
            }
        }
        case "class": {
            return {
                backgroundColor: "rgba(248, 250, 252, 0.5)",
                color: "#334155",
                iconColor: "#06B6D4", // A vibrant cyan for classes
                borderColor: "rgba(226, 232, 240, 0.8)",
            }
        }
        case "package": {
            return {
                backgroundColor: "rgba(248, 250, 252, 0.5)",
                color: "#334155",
                iconColor: "#FB923C", // A bold orange for packages
                borderColor: "rgba(226, 232, 240, 0.8)",
            }
        }
        default:
            return {
                backgroundColor: "rgba(248, 250, 252, 0.5)",
                color: "#334155",
                iconColor: "#94A3B8",
                borderColor: "rgba(226, 232, 240, 0.8)",
            }
    }
}

export default getNodeStyle;