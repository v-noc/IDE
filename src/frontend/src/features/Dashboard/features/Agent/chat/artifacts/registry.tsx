import type { ReactNode } from "react";
import { WalkthroughArtifact } from "./WalkthroughArtifact";

function UnknownArtifactChip({ doc, render }: { doc: string; render: string }) {
  return (
    <p className="rounded border border-dashed border-border px-2 py-1 text-[10px] text-muted-foreground">
      artifact ({render}): {doc}
    </p>
  );
}

export function renderArtifact(render: string, doc: string): ReactNode {
  switch (render) {
    case "walkthrough":
      return <WalkthroughArtifact doc={doc} />;
    default:
      return <UnknownArtifactChip doc={doc} render={render} />;
  }
}
