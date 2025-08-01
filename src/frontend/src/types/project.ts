export interface Project {
    key: string
    name: string
    path: string
    description: string
    createdDate: string
    lastModified: string
}

export interface ProjectNode {
    key: string;
    name: string;
    icon?: string;
    iconColor?: string;
    cardColor?: string;
    textColor?: string;
    children?: ProjectNode[];
}


