import { cn } from "@/lib/utils";

export type DetailLevel = "quick" | "normal" | "detailed";

const OPTIONS: { value: DetailLevel; label: string }[] = [
  { value: "quick", label: "Quick" },
  { value: "normal", label: "Normal" },
  { value: "detailed", label: "Detailed" },
];

interface SegmentedProps {
  value: DetailLevel;
  onChange: (value: DetailLevel) => void;
}

export function Segmented({ value, onChange }: SegmentedProps) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-xs font-semibold text-agent-text-body">Detail</span>
      <div
        className="flex gap-0 rounded-agent-field border border-agent-border-strong bg-agent-bg-inset p-[3px]"
        role="group"
        aria-label="Detail level"
      >
        {OPTIONS.map((option) => {
          const selected = value === option.value;
          return (
            <button
              key={option.value}
              type="button"
              aria-pressed={selected}
              onClick={() => onChange(option.value)}
              className={cn(
                "flex-1 rounded-[6px] py-1.5 text-xs font-semibold transition-[color,background-color,box-shadow]",
                selected
                  ? "bg-agent-border-strong text-agent-text shadow-[0_1px_2px_rgba(0,0,0,0.35),inset_0_0_0_1px_var(--agent-accent-border)] ring-1 ring-agent-accent-border/40"
                  : "bg-transparent text-agent-text-muted hover:bg-agent-bg-raised/60 hover:text-agent-text-body",
              )}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
