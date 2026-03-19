import type { WireMessage, WireTextPart } from "@/types/agent";

function isWireTextPart(p: unknown): p is WireTextPart {
  return (
    typeof p === "object" &&
    p !== null &&
    (p as WireTextPart).type === "text" &&
    typeof (p as WireTextPart).text === "string"
  );
}

export function wireMessagePlainText(message: WireMessage): string {
  return message.parts.filter(isWireTextPart).map((p) => p.text).join("\n");
}
