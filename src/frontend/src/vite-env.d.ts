/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_READ_ONLY?: string;
  /** When true, commit list in Versioning panel does not request `/commits` APIs. */
  readonly VITE_VERSIONING_COMMIT_LIST_DISABLED?: string;
}
