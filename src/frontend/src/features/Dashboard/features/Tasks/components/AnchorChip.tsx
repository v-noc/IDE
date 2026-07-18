import type { TaskAnchor } from "@/types/tasks";
import { ANCHOR_GREEN, ANCHOR_GREEN_BG, HOT_AMBER, HOT_AMBER_BG } from "../theme";

const KIND_ICONS: Record<string, string> = {
  function: "ƒ",
  class: "C",
  file: "📄",
  folder: "📁",
  call: "→",
};

interface AnchorChipProps {
  anchor: TaskAnchor;
  hot?: boolean;
  onClick?: (e: React.MouseEvent) => void;
  className?: string;
}

export function AnchorChip({ anchor, hot, onClick, className = "" }: AnchorChipProps) {
  const unresolved = anchor.is_resolved === false;
  const icon = KIND_ICONS[anchor.kind] ?? "•";

  let color = ANCHOR_GREEN;
  let bg = ANCHOR_GREEN_BG;
  if (hot) {
    color = HOT_AMBER;
    bg = HOT_AMBER_BG;
  } else if (unresolved) {
    color = HOT_AMBER;
    bg = HOT_AMBER_BG;
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-mono transition-colors hover:opacity-80 ${className}`}
      style={{ color, backgroundColor: bg, border: `1px solid ${color}44` }}
    >
      <span className="opacity-70">{icon}</span>
      <span className="truncate max-w-[120px]">{anchor.qname}</span>
      {unresolved && <span>⚠</span>}
    </button>
  );
}
