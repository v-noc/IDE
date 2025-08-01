import type { ProjectTreeResponse } from "../service/useProject";

const getNodeStyle = (node: ProjectTreeResponse) => {

    switch (node.node_type) {
        case "project":
            return {
                backgroundColor: "#CFD8DC", // Blue Grey 100 (Subtle, calm start)
                color: "#263238",           // Blue Grey 900 (Deep charcoal text)
                iconColor: "#546E7A",       // Blue Grey 600 (Muted blue-grey icon)
                borderColor: "#B0BEC5",     // Blue Grey 200
            }
        case "folder":
            return {
                backgroundColor: "#ECEFF1", // Light Blue Grey 50 (Slightly warmer off-white for main container)
                color: "#37474F",           // Blue Grey 800 (Deep slate text)
                iconColor: "#607D8B",       // Blue Grey 500 (Medium slate icon)
                borderColor: "#CFD8DC",     // Blue Grey 100
            }
        case "file":
            return {
                backgroundColor: "#FAFAFA", // Very light off-white (Child of folder, almost neutral background)
                color: "#424242",           // Grey 900 (Darker grey text)
                iconColor: "#757575",       // Grey 600 (Medium grey icon)
                borderColor: "#EEEEEE",     // Light grey 200
            }
        case "function": {
            return {
                backgroundColor: "#FDFDFD", // Clean, near-white (Grandchild, minimal base)
                color: "#A14856",           // Desaturated Red/Rose (Muted accent for function)
                iconColor: "#C68D95",       // Lighter muted red
                borderColor: "#FBEFF0",     // Very light red-tinted border
            }
        }
        case "class": {
            return {
                backgroundColor: "#FDFDFD", // Clean, near-white (Grandchild, minimal base)
                color: "#5C6F73",           // "Blue Stone" deep muted teal (Muted accent for class)
                iconColor: "#95A2A5",       // Lighter muted teal
                borderColor: "#EFF5F6",     // Very light teal-tinted border
            }
        }
        case "package": { // Using a sophisticated 'Zinc Brown' for packages
            return {
                backgroundColor: "#EFEBE9", // Brown 50 (Soft, warm muted brown)
                color: "#5D4037",           // Brown 800 (Deep brown text)
                iconColor: "#8D6E63",       // Brown 400 (Medium brown icon)
                borderColor: "#D7CCC8",     // Brown 200
            }
        }
        default: // A very neutral, subtle zinc-like tone for any unclassified nodes
            return {
                backgroundColor: "#F5F5F5", // Light Grey 100
                color: "#616161",           // Grey 700
                iconColor: "#BDBDBD",       // Grey 400
                borderColor: "#E0E0E0",     // Grey 200
            }
    }
}

export default getNodeStyle;