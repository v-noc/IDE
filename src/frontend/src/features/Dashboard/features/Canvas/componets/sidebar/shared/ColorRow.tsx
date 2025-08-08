import React from "react";
import { Input } from "@/components/ui/input";

export type ColorRowProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
};

function normalizeHex(input: string): string {
  let v = input.trim();
  if (!v.startsWith("#")) v = `#${v}`;
  return v.slice(0, 7);
}

const ColorRow: React.FC<ColorRowProps> = ({ label, value, onChange }) => {
  return (
    <div className="grid grid-cols-[auto_auto_1fr] items-center gap-2">
      <div className="text-sm text-muted-foreground whitespace-nowrap pr-1">
        {label}
      </div>
      <input
        aria-label={`${label} color`}
        type="color"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-8 w-8 p-0 border rounded"
      />
      <Input
        aria-label={`${label} hex`}
        value={value}
        onChange={(e) => onChange(normalizeHex(e.target.value))}
        placeholder="#000000"
        className="h-8"
      />
    </div>
  );
};

export default ColorRow;
