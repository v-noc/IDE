import { Button } from "@/components/ui/button";
import { Cog, Plus } from "lucide-react";

interface ConfigNotCreatedStateProps {
  onCreateConfiguration: () => void;
}

export default function ConfigNotCreatedState({
  onCreateConfiguration,
}: ConfigNotCreatedStateProps) {
  return (
    <div className="h-full w-full p-6">
      <div className="h-full w-full rounded-lg border border-dashed border-border bg-card p-8 flex items-center justify-center">
        <div className="max-w-xl text-center flex flex-col items-center gap-4">
          <div className="size-14 rounded-full bg-muted flex items-center justify-center border">
            <Cog className="size-7 text-muted-foreground" />
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-slate-800">
              Test configuration not created
            </h3>
            <p className="text-sm text-muted-foreground">
              Start by creating the test configuration for this function. After
              that, we can discover and run test cases from this panel.
            </p>
          </div>
          <Button size="sm" className="gap-2" onClick={onCreateConfiguration}>
            <Plus className="size-4" />
            Create configuration
          </Button>
        </div>
      </div>
    </div>
  );
}
