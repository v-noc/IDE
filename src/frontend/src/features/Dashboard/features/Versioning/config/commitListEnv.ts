import { toProjectApiId } from "@/lib/projectId";

function isGloballyDisabled(): boolean {
  const v = import.meta.env.VITE_VERSIONING_COMMIT_LIST_DISABLED;
  return v === "true" || v === "1";
}

function allowedProjects(): Set<string> {
  const raw = import.meta.env.VITE_VERSIONING_COMMIT_LIST_ALLOWED_PROJECTS ?? "";
  return new Set(
    raw
      .split(",")
      .map((s: string) => s.trim())
      .filter(Boolean)
      .map(toProjectApiId),
  );
}

/**
 * When true, the commit history list does not fetch commits (no API) and shows a placeholder.
 * Set in `.env`: VITE_VERSIONING_COMMIT_LIST_DISABLED=true
 *
 * Projects listed in VITE_VERSIONING_COMMIT_LIST_ALLOWED_PROJECTS (comma-separated,
 * slug or `ProjectSchema/slug`) ignore the disable flag, e.g. for demos.
 */
export function isCommitListDisabledFor(
  projectId: string | null | undefined,
): boolean {
  if (!isGloballyDisabled()) return false;
  if (!projectId) return true;
  return !allowedProjects().has(toProjectApiId(projectId));
}
