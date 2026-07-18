/**
 * API project_id — always `ProjectSchema/{slug}` (matches structure/code routes).
 * Route param is the slug only; store `projectData.id` is already prefixed.
 */
export function toProjectApiId(projectId: string | undefined | null): string {
  if (!projectId) return "";
  if (projectId.startsWith("ProjectSchema/")) return projectId;
  return `ProjectSchema/${projectId}`;
}
