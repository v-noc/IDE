/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_READ_ONLY?: string;
  /** When true, Tasks and Agent panels show an "under construction" overlay. */
  readonly VITE_UNDER_CONSTRUCTION?: string;
  /** When true, commit list in Versioning panel does not request `/commits` APIs. */
  readonly VITE_VERSIONING_COMMIT_LIST_DISABLED?: string;
  /** Comma-separated project slugs that ignore VITE_VERSIONING_COMMIT_LIST_DISABLED. */
  readonly VITE_VERSIONING_COMMIT_LIST_ALLOWED_PROJECTS?: string;
}
