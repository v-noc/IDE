import type { FieldResponse } from "@/features/Dashboard/service/useProject";
export interface FunctionNodeProps {
    id: string;
    name: string;
    qname: string;
    inputs: FieldResponse[];
    outputs: FieldResponse[];
    callOrder: number;
    icon: string;
    theme?: {
        iconColor?: string;
        cardColor?: string;
        textColor?: string;
    };
    performance?: {
        avgTime?: number;
        runCount?: number;
        successRate?: number; // 0..1
    };
    children?: FunctionNodeProps[];
    isExpanded?: boolean;
}

export interface ClassNodeProps {
    id: string;
    name: string;
    qname: string;
    icon: string;
    theme?: {
        iconColor?: string;
        cardColor?: string;
        textColor?: string;

    };
    fields: FieldResponse[];
    methods: FunctionNodeProps[];
    sourceFile: string;
    isExpanded?: boolean;
}
