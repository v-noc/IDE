import "@blocknote/core/fonts/inter.css";
import { createCodeBlockSpec } from "@blocknote/core";
import { codeBlockOptions } from "@blocknote/code-block";
import { useCreateBlockNote } from "@blocknote/react";
import { BlockNoteView } from "@blocknote/shadcn";
import "@blocknote/shadcn/style.css";
import { BlockNoteSchema } from "@blocknote/core";
import {
  SuggestionMenuController,
  getDefaultReactSlashMenuItems,
} from "@blocknote/react";
import { useEffect, useRef, useMemo } from "react";
import { FileText } from "lucide-react";
import { filterSuggestionItems } from "@blocknote/core/extensions";
import { debounce } from "remeda";
import { useUpdateDocument } from "@/services/documents";
import type { DocumentData } from "@/services/documents";

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

/**
 * Self-contained document editor component.
 *
 * Handles:
 * - Editor initialization and configuration
 * - Document loading and syncing
 * - Auto-save with debouncing
 * - Empty state display
 *
 * Usage:
 * ```tsx
 * <DocumentEditor
 *   document={selectedDocument}
 *   nodeId={nodeKey}
 *   autoSave={true}
 *   onChange={(data) => console.log('Content changed:', data)}
 * />
 * ```
 */
export function DocumentEditor({
  document,
  onChange,
  nodeId = "",
  autoSave = true,
  debounceMs = 1000,
  containerClassName = "",
}: DocumentEditorProps) {
  const editor = useCreateBlockNote({
    schema: BlockNoteSchema.create().extend({
      blockSpecs: {
        codeBlock: createCodeBlockSpec(codeBlockOptions),
      },
    }),
  });

  const applyingRemoteContent = useRef(false);
  const lastAppliedDataRef = useRef<string | null>(null);

  // API mutation for auto-save
  const updateMutation = useUpdateDocument(nodeId);

  // Debounced save function
  const saveDocumentDebounced = useMemo(
    () =>
      debounce(
        (payload: { id: string; data: string }) => {
          if (autoSave && nodeId) {
            // Update lastAppliedDataRef to the data we're about to save
            // This prevents reloading when cache updates with the same content
            lastAppliedDataRef.current = payload.data;
            updateMutation.mutate({ id: payload.id, data: payload.data });
          }
        },
        { waitMs: debounceMs }
      ),
    [autoSave, nodeId, debounceMs, updateMutation]
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

    const data = document.data ?? "";

    // Skip if we've already applied this exact content
    // Compare by value, not reference, to handle cache updates with same content
    if (lastAppliedDataRef.current === data) return;

    // Also check if the content is semantically the same (normalized JSON comparison)
    // This handles cases where cache updates might have slightly different formatting
    if (lastAppliedDataRef.current && data) {
      try {
        const currentParsed = JSON.parse(lastAppliedDataRef.current);
        const newParsed = JSON.parse(data);
        // Deep equality check for JSON content
        if (JSON.stringify(currentParsed) === JSON.stringify(newParsed)) {
          // Content is the same, just update the ref and skip reloading
          lastAppliedDataRef.current = data;
          return;
        }
      } catch {
        // If parsing fails, fall through to normal comparison
      }
    }

    applyingRemoteContent.current = true;

    const loadContent = async () => {
      try {
        // Parse JSON (BlockNote blocks)
        const parsedDocument = JSON.parse(data);

        // Validate that parsedDocument is an array of blocks
        if (Array.isArray(parsedDocument)) {
          // Validate blocks have required structure (if array is not empty)
          if (parsedDocument.length === 0) {
            // Empty content - clear editor
            editor.replaceBlocks(editor.document, []);
            lastAppliedDataRef.current = data;
            return;
          }

          const isValidBlocks = parsedDocument.every(
            (block: unknown) =>
              block &&
              typeof block === "object" &&
              block !== null &&
              "id" in block
          );

          if (isValidBlocks) {
            // Replace all blocks at once - BlockNote handles the replacement
            editor.replaceBlocks(editor.document, parsedDocument);
            lastAppliedDataRef.current = data;
            return;
          }
        }

        // If JSON parsing fails or invalid format, clear editor
        console.error("Invalid block format, clearing editor");
        editor.replaceBlocks(editor.document, []);
        lastAppliedDataRef.current = "";
      } catch (jsonErr) {
        // If JSON parsing fails, treat as empty and clear editor
        console.error("Error parsing document JSON:", jsonErr);
        try {
          editor.replaceBlocks(editor.document, []);
          lastAppliedDataRef.current = "";
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
  }, [editor, document, document?._key, document?.data]);

  // Handle content changes
  const handleChange = async (currentEditor: typeof editor) => {
    if (applyingRemoteContent.current) return;

    const jsonData = JSON.stringify(currentEditor.document);

    // Call onChange callback immediately
    onChange?.(jsonData);

    // Auto-save if enabled and document exists
    if (autoSave && document?._key && nodeId) {
      saveDocumentDebounced.call({
        id: document._key,
        data: jsonData,
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
          slashMenu={false}
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
