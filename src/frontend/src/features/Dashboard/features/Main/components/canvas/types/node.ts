export interface FunctionNodeProps {
    id: string;
    name: string;
    qname: string;
    inputs: Array<{ name: string; type: string }>;
    outputs: Array<{ name: string; type: string }>;
    callOrder: number;
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
    fields: Array<{ name: string; type: string }>;
    methods: Array<{ name: string; returnType?: string }>;
    sourceFile: string;
    isExpanded?: boolean;
}
