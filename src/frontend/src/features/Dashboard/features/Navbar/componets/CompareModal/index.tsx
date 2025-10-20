import { useMemo, useState, useCallback } from "react";
import {
  SAMPLE_DATA,
  type BranchComparisonData,
  type SymbolChangeNode,
} from "./SampleData";
import SymbolTree from "./SymbolTree";
import DiffViewer from "./DiffViewer";

type CompareModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

const CompareModal = ({ isOpen, onClose }: CompareModalProps) => {
  const [data] = useState<BranchComparisonData>(SAMPLE_DATA);
  const [selectedPath, setSelectedPath] = useState<string>(
    data.files[0]?.path || "src/parser/graphBuilder.ts"
  );

  const counts = useMemo(
    () => ({
      added: data.files.filter((f) => f.changeType === "added").length,
      removed: data.files.filter((f) => f.changeType === "removed").length,
    }),
    [data.files]
  );

  const handleSelectSymbol = useCallback(
    (node: SymbolChangeNode) => {
      const filePath = node.id.startsWith("file:")
        ? node.id.replace("file:", "")
        : selectedPath;
      setSelectedPath(filePath);
    },
    [selectedPath]
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative bg-background rounded-lg shadow-xl border w-[92vw] max-w-6xl h-[80vh] flex flex-col">
        <div className="p-3 border-b flex items-center justify-between">
          <div className="text-sm">
            Compare <span className="font-semibold">{data.base}</span> ↔{" "}
            <span className="font-semibold">{data.compare}</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2 py-0.5 rounded border bg-green-100 text-green-700">
              +{counts.added} files
            </span>
            <span className="px-2 py-0.5 rounded border bg-red-100 text-red-700">
              -{counts.removed} files
            </span>
            <div className="mx-2 h-4 w-px bg-border" />
            <button className="px-2 py-0.5 rounded border hover:bg-green-50 text-green-700 border-green-200">
              Approve all
            </button>
            <button className="px-2 py-0.5 rounded border hover:bg-amber-50 text-amber-700 border-amber-200">
              Request review
            </button>
            <button className="px-2 py-0.5 rounded border hover:bg-red-50 text-red-700 border-red-200">
              Reject all
            </button>
            <button
              className="px-2 py-0.5 rounded border hover:bg-accent"
              onClick={onClose}
            >
              Close
            </button>
          </div>
        </div>
        <div className="flex-1 grid grid-cols-12 gap-3 p-3 min-h-0">
          <div className="col-span-4 flex flex-col min-h-0">
            <div className="text-xs font-medium mb-2">
              Function/Class changes
            </div>
            <div className="flex-1 overflow-auto border rounded p-2">
              <SymbolTree nodes={data.symbols} />
            </div>
          </div>
          <div className="col-span-8 flex flex-col min-h-0">
            <div className="text-xs font-medium mb-2 flex items-center gap-2">
              <span>Diff</span>
              <span className="px-2 py-0.5 rounded border bg-muted/50 text-muted-foreground">
                {selectedPath}
              </span>
            </div>
            <div className="flex-1 overflow-auto border rounded">
              <DiffViewer diff={data.diffs[selectedPath]} />
            </div>
          </div>
        </div>
        <div className="p-3 border-t flex items-center justify-end gap-2 text-xs">
          <button className="px-2 py-0.5 rounded border hover:bg-green-50 text-green-700 border-green-200">
            Approve all
          </button>
          <button className="px-2 py-0.5 rounded border hover:bg-amber-50 text-amber-700 border-amber-200">
            Request review
          </button>
          <button className="px-2 py-0.5 rounded border hover:bg-red-50 text-red-700 border-red-200">
            Reject all
          </button>
        </div>
      </div>
    </div>
  );
};

export default CompareModal;
