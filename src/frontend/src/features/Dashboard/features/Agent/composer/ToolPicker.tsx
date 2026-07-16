import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  isAvailable,
  TOOL_REGISTRY,
  type ToolId,
  type ToolInfo,
} from "../tools/registry";
import { PickerMenu } from "./PickerMenu";

interface ToolPickerProps {
  selectedId: ToolId;
  onSelect: (id: ToolId) => void;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  disabled?: boolean;
}

function ToolPickerRow({
  tool,
  selected,
  onSelect,
}: {
  tool: ToolInfo;
  selected: boolean;
  onSelect: (id: ToolId) => void;
}) {
  const available = isAvailable(tool.id);
  const Icon = tool.icon;

  const row = (
    <button
      type="button"
      disabled={!available}
      aria-disabled={!available}
      onClick={() => {
        if (!available) return;
        onSelect(tool.id);
      }}
      className={cn(
        "flex w-full items-center gap-2.5 rounded-agent-field px-2.5 py-2 text-left transition-colors",
        available && "hover:bg-agent-bg-raised",
        selected && available && "bg-agent-bg-raised",
        !available && "cursor-not-allowed opacity-55",
      )}
    >
      <span
        className={cn(
          "flex size-[26px] shrink-0 items-center justify-center rounded-[7px] border",
          available
            ? "border-agent-accent-border bg-agent-accent-bg text-agent-accent-text"
            : "border-agent-border-strong bg-agent-bg-raised text-agent-text-muted",
        )}
      >
        <Icon className="size-3" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-[13px] font-semibold text-agent-text">
          {tool.name}
        </span>
        <span className="block text-[11px] text-agent-text-muted">
          {tool.desc}
        </span>
      </span>
      {available ? (
        <span className="shrink-0 text-[13px] text-agent-accent">
          {selected ? "✓" : ""}
        </span>
      ) : (
        <span className="shrink-0 rounded-agent-pill bg-agent-bg-raised px-2 py-0.5 font-agent-mono text-[10px] text-agent-text-faint">
          Soon
        </span>
      )}
    </button>
  );

  if (available) return row;

  return (
    <Tooltip>
      <TooltipTrigger asChild>{row}</TooltipTrigger>
      <TooltipContent side="left" className="text-xs">
        Coming soon — walkthrough is available today.
      </TooltipContent>
    </Tooltip>
  );
}

export function ToolPicker({
  selectedId,
  onSelect,
  open,
  onOpenChange,
  disabled,
}: ToolPickerProps) {
  const selected = TOOL_REGISTRY.find((tool) => tool.id === selectedId);
  const SelectedIcon = selected?.icon;

  return (
    <PickerMenu
      label="TOOLS"
      open={open}
      onOpenChange={onOpenChange}
      trigger={
        <button
          type="button"
          disabled={disabled}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-agent-field border px-2.5 py-1.5 text-xs font-semibold transition-colors",
            open
              ? "border-agent-accent bg-agent-accent-bg-subtle text-agent-accent-text"
              : "border-agent-accent-border bg-agent-accent-bg-subtle text-agent-accent-text hover:bg-agent-accent-bg",
            disabled && "cursor-not-allowed opacity-50",
          )}
        >
          {SelectedIcon ? <SelectedIcon className="size-2.5 fill-current" /> : null}
          {selected?.short ?? "Tool"}
          <span className="text-[9px] text-agent-text-agent-label">▾</span>
        </button>
      }
    >
      {TOOL_REGISTRY.map((tool) => (
        <ToolPickerRow
          key={tool.id}
          tool={tool}
          selected={tool.id === selectedId}
          onSelect={(id) => {
            onSelect(id);
            onOpenChange(false);
          }}
        />
      ))}
    </PickerMenu>
  );
}
