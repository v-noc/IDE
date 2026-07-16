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
      <div className="flex gap-0 rounded-agent-field border border-agent-border-strong bg-agent-bg-inset p-[3px]">
        {OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={cn(
              "flex-1 rounded-[6px] py-1.5 text-xs font-semibold transition-colors",
              value === option.value
                ? "bg-agent-bg-raised text-agent-text"
                : "bg-transparent text-agent-text-muted hover:text-agent-text-body",
            )}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
