import "@blocknote/core/fonts/inter.css";
import { useCreateBlockNote } from "@blocknote/react";
import { BlockNoteView } from "@blocknote/shadcn";
import "@blocknote/shadcn/style.css";
import { BlockNoteSchema, defaultBlockSpecs } from "@blocknote/core";
import { type BlockSpecs } from "@blocknote/core";
// import { ReactMermaidBlock } from "./blocks/MermaidBlock";
import {
  SuggestionMenuController,
  getDefaultReactSlashMenuItems,
} from "@blocknote/react";
import { useEffect, useRef } from "react";
import { FileText } from "lucide-react";
import { createHighlighter } from "./shiki.bundle";

// Creates a new editor instance with Mermaid block registered.
// const customBlockSpecs = {
//   mermaid: ReactMermaidBlock,
// } satisfies BlockSpecs;
const schema = BlockNoteSchema.create({
  blockSpecs: {
    ...defaultBlockSpecs,
  } as BlockSpecs,
});
type DocumentsProps = {
  document?: { id: string; data?: string };
  onChange?: (data: string) => void;
};

const Documents = ({ document, onChange }: DocumentsProps) => {
  const editor = useCreateBlockNote({
    schema,
    initialContent: undefined,
    codeBlock: {
      indentLineWithTab: true,
      defaultLanguage: "python",
      supportedLanguages: {
        python: {
          name: "Python",
          aliases: ["py"],
        },
      },
      createHighlighter: () =>
        createHighlighter({
          themes: ["github-dark"],
          langs: [],
        }),
    },
  });
  const applyingRemoteContent = useRef(false);
  const lastAppliedDataRef = useRef<string | null>(null);

  // Load content when selected document changes
  useEffect(() => {
    if (!editor || !document) return;
    const data = document?.data ?? "";

    // Skip if we've already applied this exact content
    if (lastAppliedDataRef.current === data) return;

    applyingRemoteContent.current = true;
    try {
      // Try JSON (BlockNote blocks)
      const parsedDocument = JSON.parse(data);
      editor.replaceBlocks(editor.document, parsedDocument);
      lastAppliedDataRef.current = data;
    } catch {
      // Fallback: treat as Markdown and REPLACE content (not append)
      try {
        editor.replaceBlocks(editor.document, []);
        // pasteMarkdown appends at cursor; with empty doc this effectively replaces
        // If parse-to-blocks API is available, prefer it; otherwise paste

        const blocks = editor.tryParseMarkdownToBlocks(data);
        if (!blocks) {
          editor.replaceBlocks(editor.document, blocks);
        } else {
          editor.pasteMarkdown(data);
        }

        lastAppliedDataRef.current = data;
      } catch (mdErr) {
        console.error("Error applying markdown document data:", mdErr);
      }
    } finally {
      // Let BlockNote apply the changes before re-enabling onChange propagation
      setTimeout(() => {
        applyingRemoteContent.current = false;
      }, 0);
    }
  }, [editor, document, document?.id, document?.data]);

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
          className="rounded-none docs-editor"
          theme="light"
          onChange={async (currentEditor) => {
            if (applyingRemoteContent.current) return;
            onChange?.(await currentEditor?.blocksToMarkdownLossy());
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
    </div>
  );
};

export default Documents;
