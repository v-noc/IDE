import type { WireMessagePart } from "@/types/agent";

export function wirePartType(part: WireMessagePart): string {
  if (part && typeof part === "object" && "type" in part) {
    const t = (part as { type: unknown }).type;
    if (typeof t === "string" && t.length > 0) return t.toLowerCase();
  }
  return "unknown";
}
