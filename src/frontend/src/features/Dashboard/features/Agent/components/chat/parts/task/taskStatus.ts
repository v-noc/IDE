export type VisualStatus = "completed" | "error" | "pending";

export function toVisualStatus(state: string | undefined): VisualStatus {
  const s = (state ?? "").toLowerCase();
  if (
    s.includes("complete") ||
    s === "done" ||
    s.includes("success") ||
    s === "skipped"
  ) {
    return "completed";
  }
  if (
    s.includes("fail") ||
    s.includes("error") ||
    s.includes("cancel") ||
    s === "failed"
  ) {
    return "error";
  }
  return "pending";
}
