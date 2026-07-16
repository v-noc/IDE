import type { LucideIcon } from "lucide-react";
import { AlignLeft, FileText, LayoutGrid, Play } from "lucide-react";

export type ToolId = "walkthrough" | "describe" | "document" | "group";
export type ToolStatus = "available" | "coming-soon";

export interface ToolInfo {
  id: ToolId;
  name: string;
  short: string;
  desc: string;
  runLabel: string;
  defaultPrompt: string;
  unit: string;
  icon: LucideIcon;
  status: ToolStatus;
}

export const TOOL_REGISTRY: ToolInfo[] = [
  {
    id: "walkthrough",
    name: "Code walkthrough",
    short: "Walkthrough",
    desc: "Guided step-by-step tour of a node",
    runLabel: "Run tour",
    defaultPrompt: "Generate a walkthrough of this node.",
    unit: "steps",
    icon: Play,
    status: "available",
  },
  {
    id: "describe",
    name: "Description generator",
    short: "Describe",
    desc: "Concise description of a node",
    runLabel: "Generate",
    defaultPrompt: "Describe this node.",
    unit: "calls",
    icon: AlignLeft,
    status: "coming-soon",
  },
  {
    id: "document",
    name: "Document generator",
    short: "Document",
    desc: "Full document, with editable intent",
    runLabel: "Generate doc",
    defaultPrompt: "Generate a document for this node.",
    unit: "sections",
    icon: FileText,
    status: "coming-soon",
  },
  {
    id: "group",
    name: "Grouper",
    short: "Group",
    desc: "Organize children into groups",
    runLabel: "Create groups",
    defaultPrompt: "Group the children of this node.",
    unit: "passes",
    icon: LayoutGrid,
    status: "coming-soon",
  },
];

const byId = new Map(TOOL_REGISTRY.map((tool) => [tool.id, tool]));

export function getToolInfo(toolId: string): ToolInfo | undefined {
  return byId.get(toolId as ToolId);
}

export function getDefaultAvailableTool(): ToolInfo {
  return TOOL_REGISTRY.find((tool) => tool.status === "available") ?? TOOL_REGISTRY[0];
}

export function isAvailable(toolId: string): boolean {
  return getToolInfo(toolId)?.status === "available";
}
