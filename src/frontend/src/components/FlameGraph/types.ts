export interface FlameGraphNode {
    id: string;
    name: string;
    value: number; // duration/weight
    functionId?: string;
    children?: FlameGraphNode[];
    level_name?: string; // for coloring errors
    color?: string;
}

export interface ChartNode {
    backgroundColor: string;
    color: string;
    depth: number;
    left: number;
    name: string;
    source: FlameGraphNode;
    tooltip?: string;
    width: number;
}

export interface ChartData {
    height: number;
    levels: string[][];
    nodes: Record<string, ChartNode>;
    root: string;
}

export interface ItemData {
    data: ChartData;
    focusedNode: ChartNode;
    focusNode: (uid: string) => void;
    scale: (value: number) => number;
    width: number;
    rowHeight: number;
    onSelect?: (node: FlameGraphNode) => void;
}
