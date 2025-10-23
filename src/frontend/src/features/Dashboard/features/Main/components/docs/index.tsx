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
import { useEffect } from "react";
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

  // Load content when selected document changes
  useEffect(() => {
    if (!editor || !document) return;
    // For simplicity, store raw string in a paragraph
    const data = document?.data ?? "";

    try {
      const document = JSON.parse(data);

      editor.replaceBlocks(editor.document, document);
    } catch (error) {
      editor.replaceBlocks(editor.document, []);
      console.error("Error parsing document data:", error);
    }
  }, [document?.id]);

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
    <BlockNoteView
      className="h-full w-full rounded-none"
      theme="light"
      onChange={(currentEditor) => {
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
  );
};

export default Documents;
