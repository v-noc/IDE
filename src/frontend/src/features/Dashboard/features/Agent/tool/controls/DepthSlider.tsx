import { Slider } from "@/components/ui/slider";

interface DepthSliderProps {
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  treeMax: number;
}

export function DepthSlider({
  value,
  onChange,
  min,
  max,
  treeMax,
}: DepthSliderProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline">
        <span className="text-xs font-semibold text-agent-text-body">Depth</span>
        <span className="ml-auto font-agent-mono text-[11px] text-agent-text-muted">
          {value} (this tree: max {treeMax})
        </span>
      </div>
      <Slider
        min={min}
        max={Math.max(min, max)}
        step={1}
        value={[value]}
        onValueChange={(v) => onChange(v[0] ?? min)}
        className="[&_[data-slot=slider-range]]:bg-agent-accent [&_[data-slot=slider-thumb]]:size-4 [&_[data-slot=slider-thumb]]:border-[3px] [&_[data-slot=slider-thumb]]:border-agent-bg-tool [&_[data-slot=slider-thumb]]:bg-agent-accent [&_[data-slot=slider-thumb]]:shadow-[0_0_0_1px_var(--agent-accent)] [&_[data-slot=slider-track]]:h-1 [&_[data-slot=slider-track]]:bg-agent-bg-raised"
      />
    </div>
  );
}
