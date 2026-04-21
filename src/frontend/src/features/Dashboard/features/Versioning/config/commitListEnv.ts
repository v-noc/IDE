/**
 * When true, the commit history list does not fetch commits (no API) and shows a placeholder.
 * Set in `.env`: VITE_VERSIONING_COMMIT_LIST_DISABLED=true
 */
export function isCommitListDisabled(): boolean {
  const v = import.meta.env.VITE_VERSIONING_COMMIT_LIST_DISABLED;
  return v === "true" || v === "1";
}
