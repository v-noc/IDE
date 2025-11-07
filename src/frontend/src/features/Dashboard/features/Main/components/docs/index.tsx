import "@blocknote/core/fonts/inter.css";
import { useCreateBlockNote } from "@blocknote/react";
import { BlockNoteView } from "@blocknote/shadcn";
import "@blocknote/shadcn/style.css";
import {
  BlockNoteSchema,
  defaultBlockSpecs,
  filterSuggestionItems,
} from "@blocknote/core";
import type { BlockSpecs } from "@blocknote/core";
// import { ReactMermaidBlock } from "./blocks/MermaidBlock";
import {
  SuggestionMenuController,
  getDefaultReactSlashMenuItems,
} from "@blocknote/react";
import { useEffect, useRef } from "react";
import { FileText } from "lucide-react";

// Creates a new editor instance with Mermaid block registered.
// const customBlockSpecs = {
//   mermaid: ReactMermaidBlock,
// } satisfies BlockSpecs;
const schema = BlockNoteSchema.create({
  blockSpecs: {
    ...defaultBlockSpecs,
    // ...customBlockSpecs,
  } as BlockSpecs,
});
type DocumentsProps = {
  document?: { id: string; data?: string };
  onChange?: (data: string) => void;
};

const Documents = ({ document, onChange }: DocumentsProps) => {
  const editor = useCreateBlockNote({ schema, initialContent: undefined });
  const applyingRemoteContent = useRef(false);

  // Load content when selected document changes
  useEffect(() => {
    if (!editor || !document) return;
    const data = document?.data ?? "";
    applyingRemoteContent.current = true;
    try {
      const parsedDocument = JSON.parse(data);
      editor.replaceBlocks(editor.document, parsedDocument);
    } catch (error) {
      editor.replaceBlocks(editor.document, []);
      console.error("Error parsing document data:", error);
    } finally {
      // Let BlockNote apply the changes before re-enabling onChange propagation
      setTimeout(() => {
        applyingRemoteContent.current = false;
      }, 0);
    }
  }, [editor, document]);

  // If no document is selected, show an empty state instead of editor
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

  // Renders the editor instance using a React component.
  return (
    <div className="h-full w-full overflow-auto bg-background text-foreground">
      <div className="mx-auto max-w-4xl xl:max-w-5xl px-6 sm:px-8 lg:px-16 py-12 font-sans text-[17px] leading-8 antialiased">
        <BlockNoteView
          className="rounded-none notion-like"
          theme="light"
          onChange={(currentEditor) => {
            if (applyingRemoteContent.current) return;
            onChange?.(JSON.stringify(currentEditor?.document));
          }}
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
      <style>
        {`
          /* Subtle, Notion-like typography and spacing for BlockNote */
          .notion-like,
          .notion-like .bn-editor {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI",
              Roboto, "Helvetica Neue", Arial, "Apple Color Emoji", "Segoe UI Emoji";
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
            font-size: 17px;
            line-height: 2rem;
          }
          .notion-like .bn-container {
            padding: 0 !important;
            background: transparent !important;
          }
          .notion-like .bn-default-app {
            box-shadow: none !important;
            background: transparent !important;
          }
          .notion-like .bn-block-content {
            margin: 0.25rem 0;
          }
          .notion-like h1 {
            font-size: 1.875rem;
            line-height: 2.25rem;
            font-weight: 700;
            margin: 1.25rem 0 0.5rem;
          }
          .notion-like h2 {
            font-size: 1.5rem;
            line-height: 2rem;
            font-weight: 700;
            margin: 1rem 0 0.5rem;
          }
          .notion-like p {
            margin: 0.25rem 0;
          }
          /* Code block styles */
          .notion-like pre,
          .notion-like .bn-code,
          .notion-like .bn-code-block {
            background: #0b0b0b !important;
            color: #e5e7eb !important;
            border: 1px solid #1f2937;
            border-radius: 10px;
            padding: 0.9rem 1rem;
            overflow-x: auto;
            margin: 0.75rem 0;
          }
          .notion-like pre code {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
              "Liberation Mono", "Courier New", monospace !important;
            font-size: 0.95em;
            color: #e5e7eb !important;
          }
          /* Inline code (not in block) */
          .notion-like :not(pre) > code {
            background: #f3f4f6;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 0.15rem 0.35rem;
            color: inherit !important;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
              "Liberation Mono", "Courier New", monospace !important;
            font-size: 0.95em;
          }
        `}
      </style>
    </div>
  );
};

export default Documents;
