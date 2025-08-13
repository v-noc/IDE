import React from "react";

export type ColorFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
};

const ColorField: React.FC<ColorFieldProps> = ({ label, value, onChange }) => {
  return (
    <div className="space-y-1">
      <label className="text-xs text-muted-foreground">{label}</label>
      <input
        type="color"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-8 w-12 p-0 border rounded"
      />
    </div>
  );
};

export default ColorField;
