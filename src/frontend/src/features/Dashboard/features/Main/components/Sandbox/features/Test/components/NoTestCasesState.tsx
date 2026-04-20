import { Button } from "@/components/ui/button";
import { Beaker, Play } from "lucide-react";

interface NoTestCasesStateProps {
  onCreateTest: () => void;
  onRunTests: () => void;
}

export default function NoTestCasesState({
  onRunTests,
}: NoTestCasesStateProps) {
  return (
    <div className="h-full w-full p-6">
      <div className="h-full w-full  rounded-lg border border-dashed border-border bg-card p-8 flex items-center justify-center">
        <div className="max-w-xl text-center flex flex-col items-center gap-4">
          <div className="size-14 rounded-full bg-muted flex items-center justify-center border">
            <Beaker className="size-7 text-muted-foreground" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-800">
              No test cases found
            </h3>
            <p className="text-sm text-muted-foreground">
              No tests were detected for this function yet. Create your first
              test and run it here to be seen here.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              className="gap-2"
              onClick={onRunTests}
            >
              <Play className="size-4" />
              Run tests
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
