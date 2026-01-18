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
import { useUpdateDocument } from "../../service/useDocuments";
import type { DocumentType } from "../../service/useDocuments";

export interface DocumentEditorProps {
  /**
   * The document to edit. If undefined, shows empty state.
   */
  document?: DocumentType | null;
  
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
        // Use markdown parsing to get empty blocks (safer than direct replacement)
        const emptyBlocks = editor.tryParseMarkdownToBlocks("") || [];
        if (emptyBlocks.length > 0) {
          editor.replaceBlocks(editor.document, emptyBlocks);
        }
        lastAppliedDataRef.current = null;
      } catch (err) {
        console.error("Error clearing editor:", err);
      }
      return;
    }

    const data = document.data ?? "";

    // Skip if we've already applied this exact content
    if (lastAppliedDataRef.current === data) return;

    applyingRemoteContent.current = true;
    
    const loadContent = async () => {
      try {
        // Try JSON (BlockNote blocks) first
        const parsedDocument = JSON.parse(data);
        
        // Validate that parsedDocument is an array of blocks
        if (Array.isArray(parsedDocument) && parsedDocument.length > 0) {
          // Validate blocks have required structure
          const isValidBlocks = parsedDocument.every(
            (block: any) => block && typeof block === 'object' && block.id
          );
          
          if (isValidBlocks) {
            // Replace all blocks at once - BlockNote handles the replacement
            editor.replaceBlocks(editor.document, parsedDocument);
            lastAppliedDataRef.current = data;
            return;
          }
        }
        
        // If JSON parsing fails or invalid format, fall through to markdown
        throw new Error("Invalid block format, falling back to markdown");
      } catch (jsonErr) {
        // Fallback: treat as Markdown
        try {
          if (!data.trim()) {
            // Empty content - clear editor
            const emptyBlocks = editor.tryParseMarkdownToBlocks("") || [];
            editor.replaceBlocks(editor.document, emptyBlocks);
            lastAppliedDataRef.current = data;
            return;
          }

          // Parse markdown to blocks
          const blocks = editor.tryParseMarkdownToBlocks(data);
          if (blocks && blocks.length > 0) {
            editor.replaceBlocks(editor.document, blocks);
            lastAppliedDataRef.current = data;
          } else {
            // If parsing fails, try pasteMarkdown as last resort
            editor.pasteMarkdown(data);
            lastAppliedDataRef.current = data;
          }
        } catch (mdErr) {
          console.error("Error applying document data:", mdErr);
          // On error, at least clear the lastAppliedDataRef so we can retry
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

    const markdown = await currentEditor?.blocksToMarkdownLossy();
    
    // Call onChange callback immediately
    onChange?.(markdown);

    // Auto-save if enabled and document exists
    if (autoSave && document?._key && nodeId) {
      saveDocumentDebounced.call({
        id: document._key,
        data: markdown,
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
  const defaultPadding = "mx-auto max-w-4xl xl:max-w-5xl px-6 sm:px-8 lg:px-16 py-12";
  const paddingClass = containerClassName || defaultPadding;

  return (
    <div className="h-full w-full overflow-auto bg-background text-foreground">
      <div className={`${paddingClass} font-sans text-[17px] leading-8 antialiased`}>
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

