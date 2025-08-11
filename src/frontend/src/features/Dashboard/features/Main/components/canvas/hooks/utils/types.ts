import type { FieldResponse, NodeType } from "@/features/Dashboard/service/useProject";
import type { ThemeConfig } from "@/features/Dashboard/store/useThemeStore";

export interface CommonVNode {
    id: string;
    name: string;
    description?: string | null;
    node_type: NodeType;
    qname?: string;
    icon?: string;
    theme?: ThemeConfig;
    call_order?: number | null;
    inputs?: FieldResponse[];
    outputs?: FieldResponse[];
    fields?: FieldResponse[];
    methods?: { name: string; returnType?: string; node_type: NodeType; theme?: ThemeConfig }[];
    children: CommonVNode[];
    root_id?: string;
}

export interface SelectedFromSources {
    node: CommonVNode | null;
    parent: CommonVNode | null;
}


