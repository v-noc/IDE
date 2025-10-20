import { GitBranch } from "lucide-react";
import { useMemo } from "react";

type BranchSelectorProps = {
  branches?: string[];
  value?: string;
  onChange?: (branch: string) => void;
};

const DEFAULT_BRANCHES = [
  "main",
  "develop",
  "feature/refactor-parser",
  "bugfix/logging",
];

const BranchSelector = ({
  branches = DEFAULT_BRANCHES,
  value,
  onChange,
}: BranchSelectorProps) => {
  const current = useMemo(
    () => value ?? branches[0] ?? "main",
    [value, branches]
  );

  return (
    <div className="inline-flex items-center gap-2">
      <GitBranch className="h-4 w-4 text-muted-foreground" />
      <select
        className="text-xs px-2 py-1 rounded border bg-background hover:bg-accent cursor-pointer"
        value={current}
        onChange={(e) => onChange?.(e.target.value)}
      >
        {branches.map((b) => (
          <option key={b} value={b}>
            {b}
          </option>
        ))}
      </select>
    </div>
  );
};

export default BranchSelector;
