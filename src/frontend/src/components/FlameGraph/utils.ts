import type { FlameGraphNode, ChartData, ChartNode } from "./types";

// Minimal colors for now, users can override via data ideally
// Or we use basic generation


/**
 * Deterministic color generation for function names.
 */
export const getHashedColor = (name: string, levelName?: string) => {
    if (levelName === "error") return "#ef4444"; // red-500
    if (levelName === "warning") return "#f59e0b"; // amber-500

    // Hash function name to color
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }

    // Modern palette - stronger colors for better visibility against white
    const colors = [
        "#93c5fd", // blue-300
        "#a5b4fc", // indigo-300
        "#c4b5fd", // violet-300
        "#6ee7b7", // emerald-300
        "#67e8f9", // cyan-300
        "#bae6fd", // sky-200
        "#fcd34d", // amber-300
        "#fca5a5", // red-300
        "#d8b4fe", // purple-300
    ];

    return colors[Math.abs(hash) % colors.length];
};

export function transformChartData(rawData: FlameGraphNode): ChartData {
    let uidCounter = 0;

    // Use default of 1 to avoid division by zero
    const globalMaxValue = rawData.value || 1;

    const nodes: Record<string, ChartNode> = {};
    const levels: string[][] = [];

    function convertNode(
        sourceNode: FlameGraphNode,
        depth: number,
        leftOffset: number,
        totalWidthRatio: number // normalized width of this node relative to root
    ): ChartNode {
        const {
            children,
            name,
            level_name,
        } = sourceNode;

        const uidOrCounter = sourceNode.id || `_${uidCounter}`;
        const backgroundColor = sourceNode.color || getHashedColor(name, level_name) || "#3b82f6";

        // Add this node to the node-map and assign it a UID.
        const targetNode: ChartNode = (nodes[uidOrCounter] = {
            backgroundColor,
            color: sourceNode.color ? "#ffffff" : "#1e293b", // Light text on custom colors, dark on hashed
            depth,
            left: leftOffset,
            name,
            source: sourceNode,
            width: totalWidthRatio,
        });

        // Register the node's depth within the graph.
        if (levels.length <= depth) {
            levels.push([]);
        }
        levels[depth].push(uidOrCounter);

        // Now that the current UID has been used, increment it.
        uidCounter++;

        // Process node children.
        if (Array.isArray(children) && children.length > 0) {
            // Calculate total value of all children to determine their combined width
            const childrenTotalValue = children.reduce((acc, child) => acc + (child.value || 0), 0);

            // If we want to CENTER the children group under the parent:
            // 1. Calculate the total width ratio the children will occupy.
            //    Since width is based on value/globalMaxValue, we can just use that.
            const childrenTotalWidthRatio = childrenTotalValue / globalMaxValue;

            // 2. Calculate the offset to center this block of children within the parent's width.
            //    Parent's width is 'totalWidthRatio'. 
            //    Offset = (ParentWidth - ChildrenWidth) / 2
            //    This centers the *group* of children relative to the parent.
            const centeringOffset = (totalWidthRatio - childrenTotalWidthRatio) / 2;

            // 3. Start placing children from this new offset relative to parent's left.
            let currentChildLeft = leftOffset + centeringOffset;

            children.forEach(sourceChildNode => {
                const childWidthRatio = (sourceChildNode.value || 0) / globalMaxValue;

                const targetChildNode = convertNode(
                    sourceChildNode,
                    depth + 1,
                    currentChildLeft,
                    childWidthRatio
                );

                // Advance left position for the next sibling
                currentChildLeft += targetChildNode.width;
            });
        }

        return targetNode;
    }

    // Start conversion
    convertNode(rawData, 0, 0, (rawData.value || 0) / globalMaxValue);

    const rootUid = rawData.id || '_0';

    return {
        height: levels.length,
        levels,
        nodes,
        root: rootUid,
    };
}
