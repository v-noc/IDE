import React, {
    useMemo,
    useState,
    useCallback,
    useEffect,
    useRef,
} from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { transformChartData, getPathToRoot } from "./utils";
import { ItemRenderer } from "./ItemRenderer";
import type { FlameGraphNode, ItemData, HoverInfo } from "./types";
import { cn } from "@/lib/utils";
import { Home } from "lucide-react";

// Re-export type for consumers
export type { FlameGraphNode } from "./types";

interface FlameGraphProps {
    data: FlameGraphNode[];
    /** Optional explicit width in px. Omit to let the component measure its own container. */
    width?: number;
    rowHeight?: number;
    onSelect?: (node: FlameGraphNode) => void;
    className?: string;
}

const DEFAULT_ROW_HEIGHT = 20;
const BREADCRUMB_HEIGHT = 28;

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
    const [hover, setHover] = useState<HoverInfo | null>(null);

    useEffect(() => {
        // Reset focus whenever the underlying data changes (e.g. a new trace is loaded).
        setFocusedNodeUid(chartData?.root ?? null);
        setHover(null);
    }, [chartData]);

    const focusedNode = useMemo(() => {
        if (!chartData || !focusedNodeUid) return null;
        return chartData.nodes[focusedNodeUid] || chartData.nodes[chartData.root];
    }, [chartData, focusedNodeUid]);

    const focusNode = useCallback((uid: string) => {
        setFocusedNodeUid(uid);
    }, []);

    const breadcrumbPath = useMemo(() => {
        if (!chartData || !focusedNodeUid) return [];
        return getPathToRoot(chartData, focusedNodeUid);
    }, [chartData, focusedNodeUid]);

    const containerRef = useRef<HTMLDivElement>(null);
    const [measuredWidth, setMeasuredWidth] = useState(0);

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        const observer = new ResizeObserver((entries) => {
            const entry = entries[0];
            if (entry) setMeasuredWidth(entry.contentRect.width);
        });
        observer.observe(el);
        return () => observer.disconnect();
    }, []);

    // Prefer an explicitly passed width; fall back to self-measurement so
    // consumers don't have to wire up their own ResizeObserver, and so a
    // transient 0/negative width (e.g. before a parent's own measurement
    // resolves) never breaks rendering.
    const effectiveWidth = width && width > 0 ? width : measuredWidth;

    const rowVirtualizer = useVirtualizer({
        count: chartData?.height ?? 0,
        getScrollElement: () => containerRef.current,
        estimateSize: () => rowHeight,
        overscan: 5,
    });

    const handleHover = useCallback((info: HoverInfo | null) => setHover(info), []);

    const tooltipText = useMemo(() => {
        if (!hover || !chartData) return null;
        const { node } = hover;
        const total = chartData.nodes[chartData.root]?.source.value || 0;
        const parent = node.parentUid ? chartData.nodes[node.parentUid] : null;
        const pctOfTotal = total > 0 ? (node.source.value / total) * 100 : 0;
        const pctOfParent =
            parent && parent.source.value > 0
                ? (node.source.value / parent.source.value) * 100
                : null;
        return {
            name: node.name,
            value: node.source.value,
            pctOfTotal,
            pctOfParent,
        };
    }, [hover, chartData]);

    return (
        <div className={cn("flex flex-col h-full w-full min-h-0", className)}>
            {chartData && focusedNode && breadcrumbPath.length > 0 && (
                <div
                    className="flex items-center gap-1 overflow-x-auto whitespace-nowrap border-b border-border px-2 text-[11px] text-muted-foreground scrollbar-thin"
                    style={{ height: BREADCRUMB_HEIGHT, minHeight: BREADCRUMB_HEIGHT }}
                >
                    {breadcrumbPath.map((uid, i) => {
                        const node = chartData.nodes[uid];
                        const isActive = uid === focusedNodeUid;
                        return (
                            <React.Fragment key={uid}>
                                {i > 0 && <span className="text-border">/</span>}
                                <button
                                    type="button"
                                    onClick={() => focusNode(uid)}
                                    disabled={isActive}
                                    className={cn(
                                        "shrink-0 rounded px-1.5 py-0.5 transition-colors",
                                        isActive
                                            ? "font-medium text-foreground cursor-default"
                                            : "hover:bg-muted hover:text-foreground cursor-pointer"
                                    )}
                                    title={node.name}
                                >
                                    {i === 0 && <Home className="inline size-3 mr-1 -mt-px" />}
                                    {node.name}
                                </button>
                            </React.Fragment>
                        );
                    })}
                </div>
            )}

            <div
                ref={containerRef}
                className="relative flex-1 min-h-0 select-none overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-slate-200"
            >
                {!chartData ? (
                    <div className="flex h-full w-full items-center justify-center text-sm text-muted-foreground">
                        No data to display
                    </div>
                ) : effectiveWidth <= 0 ? null : (
                    focusedNode && (
                        <div
                            style={{
                                height: `${rowVirtualizer.getTotalSize()}px`,
                                width: "100%",
                                position: "relative",
                            }}
                        >
                            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                                const itemData: ItemData = {
                                    data: chartData,
                                    focusedNode,
                                    focusNode,
                                    scale: (value: number) =>
                                        (value / focusedNode.width) * effectiveWidth,
                                    width: effectiveWidth,
                                    rowHeight,
                                    onSelect,
                                    onHover: handleHover,
                                };
                                return (
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
                                );
                            })}
                        </div>
                    )
                )}

                {tooltipText && hover && (
                    <div
                        className="pointer-events-none fixed z-50 max-w-xs rounded-md border border-border bg-popover px-2 py-1.5 text-xs text-popover-foreground shadow-md"
                        style={{
                            left: hover.clientX + 12,
                            top: hover.clientY + 12,
                        }}
                    >
                        <div className="font-medium truncate">{tooltipText.name}</div>
                        <div className="text-muted-foreground">
                            {tooltipText.value.toFixed(2)}ms
                            {" · "}
                            {tooltipText.pctOfTotal.toFixed(1)}% of total
                            {tooltipText.pctOfParent != null &&
                                ` · ${tooltipText.pctOfParent.toFixed(1)}% of parent`}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
