/**
 * Build a shareable `/project/:id` URL with a `focus` query (encoded for ids with `/`, etc.).
 * `share` is accepted as an alias when opening links.
 */
export function buildProjectNodeShareUrl(
  projectRouteId: string,
  nodeId: string,
): string {
  const u = new URL(
    `${window.location.origin}/project/${encodeURIComponent(projectRouteId)}`,
  );
  u.searchParams.set("focus", nodeId);
  return u.toString();
}

export function pickFocusNodeIdFromSearchParams(
  searchParams: URLSearchParams,
): string | null {
  const raw = searchParams.get("focus") ?? searchParams.get("share");
  if (raw == null || raw === "") return null;
  try {
    const id = decodeURIComponent(raw);
    return id || null;
  } catch {
    return null;
  }
}

export function stripFocusSearchParams(prev: URLSearchParams): URLSearchParams {
  const next = new URLSearchParams(prev);
  next.delete("focus");
  next.delete("share");
  return next;
}
