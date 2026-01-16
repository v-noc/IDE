import React, { CSSProperties } from "react";
import { LabeledRect } from "./LabeledRect";
import type { ItemData } from "./types";

interface ItemRendererProps {
    data: ItemData;
    index: number;
    style: CSSProperties;
}

export const ItemRenderer: React.FC<ItemRendererProps> = ({
    data,
    index,
    style,
}) => {
    const { data: chartData, focusedNode, focusNode, scale, onSelect } = data;

    const uids = chartData.levels[index];
    const focusedNodeLeft = focusedNode.left;
    const focusedNodeWidth = focusedNode.width;

    return (
        <svg style={style} className="block overflow-visible center">
            {uids.map((uid: string) => {
                const node = chartData.nodes[uid];
                const nodeLeft = node.left;
                const nodeWidth = node.width;

                // If node is completely to the left or right of the focused node, skip it
                if (
                    nodeLeft + nodeWidth <= focusedNodeLeft ||
                    nodeLeft >= focusedNodeLeft + focusedNodeWidth
                ) {
                    return null;
                }

                const relativeX = nodeLeft - focusedNodeLeft;
                const x = scale(relativeX);
                const w = scale(nodeWidth);

                // Ensure width is at least 0 to prevent SVG errors
                // SVG rects cannot have negative width
                if (w < 0) return null;

                return (
                    <LabeledRect
                        key={uid}
                        backgroundColor={node.backgroundColor}
                        color={node.color}
                        height={data.rowHeight}
                        isDimmed={index < focusedNode.depth}
                        label={node.name}
                        onClick={() => {
                            focusNode(uid);
                            onSelect?.(node.source);
                        }}
                        width={w}
                        x={x}
                        y={0} // FixedSizeList handles Y via style
                        tooltip={`${node.name} (${node.source.value.toFixed(2)}ms)`}
                    />
                );
            })}
        </svg>
    );
};
