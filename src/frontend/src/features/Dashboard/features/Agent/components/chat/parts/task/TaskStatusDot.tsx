import { CheckCircle2, Circle, XCircle } from "lucide-react";
import type { VisualStatus } from "./taskStatus";

export function TaskStatusDot({ status }: { status: VisualStatus }) {
  if (status === "completed") {
    return (
      <CheckCircle2
        className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400"
        aria-hidden
      />
    );
  }
  if (status === "error") {
    return <XCircle className="h-4 w-4 shrink-0 text-destructive" aria-hidden />;
  }
  return (
    <Circle
      className="h-3.5 w-3.5 shrink-0 text-muted-foreground/70"
      aria-hidden
    />
  );
}
