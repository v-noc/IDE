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
import { ReactMermaidBlock } from "./blocks/MermaidBlock";
import {
  SuggestionMenuController,
  getDefaultReactSlashMenuItems,
} from "@blocknote/react";

// Creates a new editor instance with Mermaid block registered.
const customBlockSpecs = {
  mermaid: ReactMermaidBlock,
} satisfies BlockSpecs;
const schema = BlockNoteSchema.create({
  blockSpecs: {
    ...defaultBlockSpecs,
    ...customBlockSpecs,
  } as BlockSpecs,
});
const Documents = () => {
  const editor = useCreateBlockNote({ schema });
  // Renders the editor instance using a React component.
  return (
    <BlockNoteView
      className="h-full w-full"
      theme="light"
      editor={editor}
      slashMenu={false}
    >
      <SuggestionMenuController
        triggerCharacter="/"
        getItems={async (query: string) => {
          const defaults = getDefaultReactSlashMenuItems(editor);
          const custom: Array<{
            title: string;
            subtext?: string;
            aliases?: string[];
            onItemClick: () => void;
          }> = [
            {
              title: "Mermaid diagram",
              subtext: "Insert a Mermaid block",
              aliases: ["mermaid", "diagram", "graph"],
              onItemClick: () => {
                const ref = editor.getTextCursorPosition().block;
                editor.insertBlocks(
                  [
                    {
                      // The custom schema registers this block type
                      type: "mermaid" as unknown as keyof typeof editor.schema.blockSchema,
                      props: {
                        code: "flowchart TD\nA[Start] --> B[End]",
                        textAlignment: "center",
                        showPreview: true,
                      } as Record<string, unknown>,
                    } as unknown as Parameters<
                      typeof editor.insertBlocks
                    >[0][number],
                  ],
                  ref,
                  "after"
                );
              },
            },
          ];
          return filterSuggestionItems([...custom, ...defaults], query);
        }}
      />
    </BlockNoteView>
  );
};

export default Documents;
