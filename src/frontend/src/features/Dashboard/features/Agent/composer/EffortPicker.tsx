import { cn } from "@/lib/utils";
import type { EffortLevel } from "../stream/types";
import { PickerMenu } from "./PickerMenu";

const EFFORT_OPTIONS: {
  value: EffortLevel;
  label: string;
  hint: string;
}[] = [
  { value: "off", label: "Off", hint: "no visible thinking" },
  { value: "low", label: "Low", hint: "brief thinking" },
  { value: "medium", label: "Medium", hint: "balanced — the settings default" },
  { value: "high", label: "High", hint: "thorough thinking, slower" },
];

interface EffortPickerProps {
  value: EffortLevel;
  onChange: (value: EffortLevel) => void;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  disabled?: boolean;
}

export function EffortPicker({
  value,
  onChange,
  open,
  onOpenChange,
  disabled,
}: EffortPickerProps) {
  return (
    <PickerMenu
      label="REASONING EFFORT"
      open={open}
      onOpenChange={onOpenChange}
      widthClassName="w-[220px]"
      trigger={
        <button
          type="button"
          disabled={disabled}
          className={cn(
            "rounded-agent-field px-2 py-1.5 font-agent-mono text-[11px] text-agent-text-faint transition-colors hover:text-agent-text-muted",
            open && "text-agent-accent-text",
            disabled && "cursor-not-allowed opacity-50",
          )}
        >
          ◇ {value}
        </button>
      }
    >
      {EFFORT_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => {
            onChange(option.value);
            onOpenChange(false);
          }}
          className={cn(
            "flex w-full items-center gap-2.5 rounded-agent-field px-2.5 py-2 text-left transition-colors hover:bg-agent-bg-raised",
            option.value === value && "bg-agent-bg-raised",
          )}
        >
          <span className="flex size-[26px] shrink-0 items-center justify-center rounded-[7px] border border-agent-border-strong bg-agent-bg-raised font-agent-mono text-[11px] text-agent-text-muted">
            ◇
          </span>
          <span className="min-w-0 flex-1">
            <span className="block text-[13px] font-semibold capitalize text-agent-text">
              {option.label}
            </span>
            <span className="block text-[11px] text-agent-text-muted">
              {option.hint}
            </span>
          </span>
          <span className="shrink-0 text-[13px] text-agent-accent">
            {option.value === value ? "✓" : ""}
          </span>
        </button>
      ))}
    </PickerMenu>
  );
}
