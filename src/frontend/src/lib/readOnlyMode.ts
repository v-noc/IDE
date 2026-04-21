/**
 * When true, mutating HTTP methods are blocked client-side and the demo read-only dialog is shown.
 * Set in `.env`: VITE_READ_ONLY=true
 */
export function isReadOnlyMode(): boolean {
  const v = import.meta.env.VITE_READ_ONLY;
  return v === "true" || v === "1";
}

const MUTATION_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export function isWriteHttpMethod(method: string): boolean {
  return MUTATION_METHODS.has(method.toUpperCase());
}
