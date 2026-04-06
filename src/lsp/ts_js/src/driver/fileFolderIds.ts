import { existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { FILE_SCHEMA, FOLDER_SCHEMA } from "./constants";
import {
  extractMetadata,
  injectModuleMetadata,
  peelLeadingJsDoc,
  splitShebangAndBom,
} from "./moduleMetadata";

function randomIdFallback(): string {
  return crypto.randomUUID();
}

/** Same behavior as Python `read_or_inject_file_id` (module docstring → leading JSDoc). */
export function readOrInjectFileId(filePath: string): {
  file_id: string;
  modified: boolean;
} {
  let content: string;
  try {
    content = readFileSync(filePath, "utf8");
  } catch {
    return { file_id: randomIdFallback(), modified: false };
  }

  try {
    const { rest } = splitShebangAndBom(content);
    const { inner } = peelLeadingJsDoc(rest);
    const meta = extractMetadata(inner);
    const existing = meta.FileID;
    if (existing) {
      return { file_id: `${FILE_SCHEMA}/${existing}`, modified: false };
    }

    const fileId = crypto.randomUUID();
    const { content: next, modified } = injectModuleMetadata(content, {
      FileID: fileId,
    });
    if (modified) {
      try {
        writeFileSync(filePath, next, "utf8");
      } catch {
        // return id anyway; Python writes best-effort
      }
    }
    return { file_id: `${FILE_SCHEMA}/${fileId}`, modified };
  } catch {
    return { file_id: randomIdFallback(), modified: false };
  }
}

const FOLDER_INDEX_CANDIDATES = [
  "index.ts",
  "index.tsx",
  "index.js",
  "index.jsx",
  "index.mjs",
  "index.cjs",
  "index.mts",
  "index.cts",
];

function resolveFolderMarkerFile(folderPath: string): string {
  for (const name of FOLDER_INDEX_CANDIDATES) {
    const p = path.join(folderPath, name);
    if (existsSync(p)) return p;
  }
  const fallback = path.join(folderPath, "index.ts");
  writeFileSync(fallback, "", "utf8");
  return fallback;
}

/** Same behavior as Python `read_or_inject_folder_id` (`__init__.py` → `index.ts` chain). */
export function readOrInjectFolderId(folderPath: string): {
  folder_id: string;
  modified: boolean;
} {
  const markerPath = resolveFolderMarkerFile(folderPath);

  let content: string;
  try {
    content = readFileSync(markerPath, "utf8");
  } catch {
    return { folder_id: randomIdFallback(), modified: false };
  }

  try {
    const { rest } = splitShebangAndBom(content);
    const { inner } = peelLeadingJsDoc(rest);
    const meta = extractMetadata(inner);
    const existing = meta.FolderID;
    if (existing) {
      return { folder_id: `${FOLDER_SCHEMA}/${existing}`, modified: false };
    }

    const folderId = crypto.randomUUID();
    const { content: next, modified } = injectModuleMetadata(content, {
      FolderID: folderId,
    });
    if (modified) {
      try {
        writeFileSync(markerPath, next, "utf8");
      } catch {
        //
      }
    }
    return { folder_id: `${FOLDER_SCHEMA}/${folderId}`, modified };
  } catch {
    return { folder_id: randomIdFallback(), modified: false };
  }
}
