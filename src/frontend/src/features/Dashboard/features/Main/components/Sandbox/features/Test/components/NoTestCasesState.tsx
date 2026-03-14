import { Button } from "@/components/ui/button";
import { Beaker, Play, Plus } from "lucide-react";

interface NoTestCasesStateProps {
  onCreateTest: () => void;
  onRunTests: () => void;
  onLoadMockDetectedTests: () => void;
}

export default function NoTestCasesState({
  onCreateTest,
  onRunTests,
  onLoadMockDetectedTests,
}: NoTestCasesStateProps) {
  return (
    <div className="h-full w-full rounded-lg border border-dashed bg-white p-8 flex items-center justify-center">
      <div className="max-w-xl text-center flex flex-col items-center gap-4">
        <div className="size-14 rounded-full bg-muted flex items-center justify-center border">
          <Beaker className="size-7 text-muted-foreground" />
        </div>
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-slate-800">No test cases found</h3>
          <p className="text-sm text-muted-foreground">
            No tests were detected for this function yet. Create your first test and
            run it here to validate behavior and catch regressions early.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" className="gap-2" onClick={onCreateTest}>
            <Plus className="size-4" />
            Create first test
          </Button>
          <Button size="sm" variant="outline" className="gap-2" onClick={onRunTests}>
            <Play className="size-4" />
            Run tests
          </Button>
          <Button size="sm" variant="ghost" onClick={onLoadMockDetectedTests}>
            Load mock detected tests
          </Button>
        </div>
      </div>
    </div>
  );
}
