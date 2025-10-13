import BaseNode from "@/features/Dashboard/features/Main/components/canvas/nodes/BaseNode";

export type NodeType = "container" | "function" | "class" | "call" | "file" | "folder" | "project"


export interface BaseNode {
    _key: string;
    _id: string
    created_at: string;
    updated_at: string;
    name: string
    description: string;
    node_type: NodeType
    qname?: string

}

export interface ThemeConfig {
    navbarColor?: string
    leftSidebarColor?: string
    rightSidebarColor?: string
    backgroundColor?: string
    textColor?: string
    iconColor?: string
    cardColor?: string
}


export interface ContainerNode extends BaseNode {
    theme_config?: ThemeConfig
    icon?: string
}

export interface CodePosition {
    line_no: number
    col_offset: number
    end_line_no: number
    end_col_offset: number
}

export interface FunctionNode extends ContainerNode {
    node_type: 'function'
    position: CodePosition

}

export interface ClassNode extends ContainerNode {
    node_type: "class"
    implements: string[]
    position: CodePosition
}

export interface CallNode extends ContainerNode {
    node_type: "call"
    position: CodePosition
}

export interface FileNode extends ContainerNode {
    node_type: "file"
    path: string
}

export interface FolderNode extends ContainerNode {
    node_type: "folder"
    path: string
}

export interface ProjectNode extends ContainerNode {
    node_type: "project"
    path: string
}

// Tree

export interface ContainerNodeTree extends ContainerNode {
    children: AnyNodeTree[]
}

export interface CallNodeTree extends CallNode {
    children: CallNodeTree[]
    target: FunctionNode | ClassNode
}

export interface FunctionNodeTree extends FunctionNode {
    children: (FunctionNodeTree | CallNodeTree | ClassNodeTree)[]
}

export interface ClassNodeTree extends ClassNode {
    children: (FunctionNodeTree | ClassNodeTree | CallNodeTree)[]
}

export interface FileNodeTree extends FileNode {
    children: (FunctionNodeTree | ClassNodeTree | CallNodeTree)[]
}

export interface FolderNodeTree extends FolderNode {
    children: (FileNodeTree | FolderNodeTree)[]
}

export interface ProjectNodeTree extends ProjectNode {
    children: (FolderNode | FileNodeTree)[]
}

export type AnyNodeTree = ProjectNodeTree | FolderNodeTree | FileNodeTree | FunctionNodeTree | ClassNodeTree | CallNodeTree