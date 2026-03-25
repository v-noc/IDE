import "@blocknote/core/fonts/inter.css";
import { createCodeBlockSpec } from "@blocknote/core";
import { codeBlockOptions } from "@blocknote/code-block";
import { useCreateBlockNote } from "@blocknote/react";
import { BlockNoteView } from "@blocknote/shadcn";
import "@blocknote/shadcn/style.css";
import { BlockNoteSchema, type PartialBlock } from "@blocknote/core";

import {
  SuggestionMenuController,
  getDefaultReactSlashMenuItems,
  useExtension,
} from "@blocknote/react";
import { useEffect, useRef, useMemo } from "react";
import { FileText } from "lucide-react";
import { filterSuggestionItems } from "@blocknote/core/extensions";
import { debounce } from "remeda";
import { useUpdateDocument } from "@/services/documents";
import type { DocumentData } from "@/services/documents";
import { VersionDiffExtension } from "./Version";
import { useDocumentDiff } from "./hooks/useDocumentDiff";

/** Non-empty BlockNote JSON block array, or null to fall back to markdown / empty. */
function parseBlockNoteJsonBlocks(trimmedJson: string): PartialBlock[] | null {
  try {
    const parsed: unknown = JSON.parse(trimmedJson);
    if (!Array.isArray(parsed) || parsed.length === 0) {
      return null;
    }
    const valid = parsed.every(
      (block: unknown) =>
        block &&
        typeof block === "object" &&
        block !== null &&
        "id" in block,
    );
    return valid ? (parsed as PartialBlock[]) : null;
  } catch {
    return null;
  }
}

/** Stable key for skip-reload: prefer JSON blocks when valid, else markdown, else empty. */
function documentContentFingerprint(jsonSource: string, markdownSource: string): string {
  const jt = (jsonSource ?? "").trim();
  if (jt) {
    const blocks = parseBlockNoteJsonBlocks(jt);
    if (blocks) {
      return `j:${JSON.stringify(blocks)}`;
    }
  }
  const mt = (markdownSource ?? "").trim();
  if (mt) {
    return `m:${mt}`;
  }
  return "e";
}

export interface DocumentEditorProps {
  /**
   * The document to edit. If undefined, shows empty state.
   */
  document?: DocumentData | null;

  /**
   * Optional callback when document content changes.
   * Called immediately (debouncing is handled internally).
   */
  onChange?: (data: string) => void;

  /**
   * Optional node ID for API calls. Required if auto-save is enabled.
   */
  nodeId?: string;

  /**
   * Project ID for API calls. Required if auto-save is enabled.
   */
  projectId?: string;

  /**
   * Whether to auto-save changes to the API. Defaults to true.
   */
  autoSave?: boolean;

  /**
   * Debounce delay in milliseconds for auto-save. Defaults to 1000ms.
   */
  debounceMs?: number;

  /**
   * Custom padding class for the editor container.
   */
  containerClassName?: string;
}

export function DocumentEditor({
  document,
  onChange,
  nodeId = "",
  projectId = "",
  autoSave = true,
  debounceMs = 1000,
  containerClassName = "",
}: DocumentEditorProps) {
  const editor = useCreateBlockNote({
    extensions: [VersionDiffExtension()],
    schema: BlockNoteSchema.create().extend({
      blockSpecs: {
        codeBlock: createCodeBlockSpec(codeBlockOptions),
      },
    }),
  });
  const versionDiff = useExtension(VersionDiffExtension, { editor });

  const applyingRemoteContent = useRef(false);
  const lastAppliedDataRef = useRef<string | null>(null);

  // API mutation for auto-save
  const updateMutation = useUpdateDocument(nodeId, projectId);
  const { isDiffActive } = useDocumentDiff({
    projectId,
    nodeId,
    document,
    versionDiff,
  });
  const jsonSource = isDiffActive
    ? (document?.compare_to?.data ?? document?.data ?? "")
    : (document?.data ?? "");
  const markdownSource = isDiffActive
    ? (document?.compare_to?.markdown ?? document?.markdown ?? "")
    : (document?.markdown ?? "");

  // Debounced save function
  const saveDocumentDebounced = useMemo(
    () =>
      debounce(
        (payload: { id: string; node_id: string; data: string; markdown: string }) => {
          if (autoSave && nodeId && projectId) {
            // Match fingerprint logic in the load effect to avoid a reload flash after save
            lastAppliedDataRef.current = documentContentFingerprint(
              payload.data,
              payload.markdown,
            );
            updateMutation.mutate({
              id: payload.id,
              node_id: payload.node_id,
              data: payload.data,
              markdown: payload.markdown,
            });
          }
        },
        { waitMs: debounceMs },
      ),
    [autoSave, nodeId, projectId, debounceMs, updateMutation],
  );

  // Load content when document changes
  useEffect(() => {
    if (!editor) return;

    if (!document) {
      // Clear editor if no document
      try {
        // Replace with empty blocks array
        editor.replaceBlocks(editor.document, []);
        lastAppliedDataRef.current = null;
      } catch (err) {
        console.error("Error clearing editor:", err);
      }
      return;
    }

    const fingerprint = documentContentFingerprint(jsonSource, markdownSource);
    if (lastAppliedDataRef.current === fingerprint) return;

    applyingRemoteContent.current = true;

    const loadContent = async () => {
      try {
        const trimmedJson = (jsonSource ?? "").trim();
        const blocksFromJson = trimmedJson
          ? parseBlockNoteJsonBlocks(trimmedJson)
          : null;

        if (blocksFromJson) {
          editor.replaceBlocks(editor.document, blocksFromJson);
          lastAppliedDataRef.current = fingerprint;
          return;
        }

        const trimmedMd = (markdownSource ?? "").trim();
        if (trimmedMd) {
          const mdBlocks = editor.tryParseMarkdownToBlocks(trimmedMd);
          editor.replaceBlocks(editor.document, mdBlocks);
          lastAppliedDataRef.current = fingerprint;
          return;
        }

        editor.replaceBlocks(editor.document, []);
        lastAppliedDataRef.current = fingerprint;
      } catch (err) {
        console.error("Error loading document content:", err);
        try {
          editor.replaceBlocks(editor.document, []);
          lastAppliedDataRef.current = fingerprint;
        } catch (clearErr) {
          console.error("Error clearing editor:", clearErr);
          lastAppliedDataRef.current = null;
        }
      } finally {
        // Let BlockNote apply the changes before re-enabling onChange propagation
        setTimeout(() => {
          applyingRemoteContent.current = false;
        }, 100);
      }
    };

    loadContent();
  }, [
    editor,
    document,
    document?.id,
    jsonSource,
    markdownSource,
    isDiffActive,
  ]);

  // Handle content changes
  const handleChange = async (currentEditor: typeof editor) => {
    if (applyingRemoteContent.current) return;

    const jsonData = JSON.stringify(currentEditor.document);
    const markdown = currentEditor.blocksToMarkdownLossy(currentEditor.document);

    // Call onChange callback immediately
    onChange?.(jsonData);

    // Auto-save if enabled and document exists
    if (autoSave && document?.id && nodeId && projectId) {
      saveDocumentDebounced.call({
        id: document.id,
        node_id: nodeId,
        data: jsonData,
        markdown,
      });
    }
  };

  // Empty state
  if (!document) {
    return (
      <div className="h-full w-full flex items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full border bg-background">
            <FileText className="h-6 w-6 text-muted-foreground" />
          </div>
          <div className="text-sm font-medium">No document selected</div>
          <div className="text-xs text-muted-foreground">
            Create a document from the sidebar to start.
          </div>
        </div>
      </div>
    );
  }

  // Editor view
  const defaultPadding =
    "mx-auto max-w-4xl xl:max-w-5xl px-6 sm:px-8 lg:px-16 py-12";
  const paddingClass = containerClassName || defaultPadding;

  return (
    <div className="h-full w-full overflow-auto bg-background text-foreground">
      <div
        className={`${paddingClass} font-sans text-[17px] leading-8 antialiased`}
      >
        <BlockNoteView
          className="rounded-none docs-editor"
          theme="light"
          onChange={handleChange}
          editor={editor}
          slashMenu={!isDiffActive}
          editable={!isDiffActive}
        >
          <SuggestionMenuController
            triggerCharacter="/"
            getItems={async (query: string) => {
              const defaults = getDefaultReactSlashMenuItems(editor);
              return filterSuggestionItems([...defaults], query);
            }}
          />
        </BlockNoteView>
      </div>
    </div>
  );
}
