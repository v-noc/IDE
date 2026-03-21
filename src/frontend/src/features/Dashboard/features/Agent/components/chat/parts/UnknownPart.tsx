import type { WireMessagePart } from "@/types/agent";
import { wirePartType } from "../partTypes";

export function UnknownPart({ part }: { part: WireMessagePart }) {
  const t = wirePartType(part);
  return (
    <div className="rounded-md border border-amber-500/40 bg-amber-500/5 p-2 text-xs text-amber-900 dark:text-amber-200">
      <p className="mb-1 font-semibold">Unsupported part type: {t}</p>
      <pre className="max-h-32 overflow-auto rounded bg-background/60 p-2 font-mono text-[10px] leading-snug">
        {JSON.stringify(part, null, 2)}
      </pre>
    </div>
  );
}
