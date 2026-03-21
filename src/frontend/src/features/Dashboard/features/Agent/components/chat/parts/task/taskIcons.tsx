import type { LucideIcon } from "lucide-react";
import { Bot, Cpu, Layers, Sparkles, Workflow } from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  sparkles: Sparkles,
  cpu: Cpu,
  workflow: Workflow,
  layers: Layers,
  bot: Bot,
};

export function resolveTaskIcon(name?: string): LucideIcon {
  if (!name?.trim()) return Layers;
  const key = name.trim().toLowerCase();
  return ICONS[key] ?? Layers;
}
