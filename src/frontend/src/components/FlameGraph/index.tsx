import React, {
    useMemo,
    useState,
    useCallback,
    useEffect,
    useRef,
} from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { transformChartData } from "./utils";
import { ItemRenderer } from "./ItemRenderer";
import type { FlameGraphNode, ItemData } from "./types";
import { cn } from "@/lib/utils";

// Re-export type for consumers
export type { FlameGraphNode } from "./types";

interface FlameGraphProps {
    data: FlameGraphNode[];
    width: number;
    rowHeight?: number;
    onSelect?: (node: FlameGraphNode) => void;
    className?: string;
    disableDefaultTooltips?: boolean;
}

const DEFAULT_ROW_HEIGHT = 20;

export const FlameGraph: React.FC<FlameGraphProps> = ({
    data,
    width,
    rowHeight = DEFAULT_ROW_HEIGHT,
    onSelect,
    className,
}) => {
    // Convert recursive data to flat ChartData structure
    const chartData = useMemo(() => {
        if (!data || data.length === 0) return null;
        return transformChartData(data[0]);
    }, [data]);

    const [focusedNodeUid, setFocusedNodeUid] = useState<string | null>(null);

    useEffect(() => {
        if (chartData && !focusedNodeUid) {
            setFocusedNodeUid(chartData.root);
        }
    }, [chartData, focusedNodeUid]);

    const focusedNode = useMemo(() => {
        if (!chartData || !focusedNodeUid) return null;
        return chartData.nodes[focusedNodeUid] || chartData.nodes[chartData.root];
    }, [chartData, focusedNodeUid]);

    const focusNode = useCallback((uid: string) => {
        setFocusedNodeUid(uid);
    }, []);

    const parentRef = useRef<HTMLDivElement>(null);

    const rowVirtualizer = useVirtualizer({
        count: chartData?.height ?? 0,
        getScrollElement: () => parentRef.current,
        estimateSize: () => rowHeight,
        overscan: 5,
    });

    if (!chartData || !focusedNode) return null;

    const itemData: ItemData = {
        data: chartData,
        focusedNode,
        focusNode,
        scale: (value: number) => (value / focusedNode.width) * width,
        width,
        rowHeight,
        onSelect,
    };

    return (
        <div
            ref={parentRef}
            className={cn(
                "select-none overflow-y-auto overflow-x-hidden h-full scrollbar-thin scrollbar-thumb-slate-200",
                className
            )}
        >
            <div
                style={{
                    height: `${rowVirtualizer.getTotalSize()}px`,
                    width: "100%",
                    position: "relative",
                }}
            >
                {rowVirtualizer.getVirtualItems().map((virtualRow) => (
                    <ItemRenderer
                        key={virtualRow.index}
                        data={itemData}
                        index={virtualRow.index}
                        style={{
                            position: "absolute",
                            top: 0,
                            left: 0,
                            width: "100%",
                            height: `${virtualRow.size}px`,
                            transform: `translateY(${virtualRow.start}px)`,
                        }}
                    />
                ))}
            </div>
        </div>
    );
};
