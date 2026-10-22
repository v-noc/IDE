import { Construction } from "lucide-react";

/** Controlled by `.env`: VITE_UNDER_CONSTRUCTION=true */
export function isUnderConstruction(): boolean {
  const v = import.meta.env.VITE_UNDER_CONSTRUCTION;
  return v === "true" || v === "1";
}

/** Covers the nearest `relative` parent. Renders nothing when the flag is off. */
export function UnderConstructionOverlay() {
  if (!isUnderConstruction()) return null;

  return (
    <div className="absolute inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-background/90 backdrop-blur-sm">
      <Construction className="size-12 text-yellow-400" />
      <span className="text-sm font-medium text-muted-foreground">
        Under construction
      </span>
    </div>
  );
}
