import { useSidebarModalStore } from "@/features/Dashboard/store/useSidebarModalStore";
import { isReadOnlyMode } from "@/lib/readOnlyMode";

export class ReadOnlyModeError extends Error {
  constructor(message = "Write operations are disabled in this environment.") {
    super(message);
    this.name = "ReadOnlyModeError";
  }
}

/**
 * Call before any write (POST/PUT/PATCH/DELETE) that bypasses `api()` (e.g. raw fetch).
 * When read-only mode is on: opens the demo dialog and throws {@link ReadOnlyModeError}.
 */
export function blockWriteIfReadOnly(): void {
  if (!isReadOnlyMode()) return;
  useSidebarModalStore.getState().openReadOnlyModal();
  throw new ReadOnlyModeError();
}
