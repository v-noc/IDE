import "@blocknote/core/fonts/inter.css";
import { useCreateBlockNote } from "@blocknote/react";
import { BlockNoteView } from "@blocknote/shadcn";
import "@blocknote/shadcn/style.css";

const Documents = () => {
  // Creates a new editor instance.
  const editor = useCreateBlockNote();
  // Renders the editor instance using a React component.
  return (
    <BlockNoteView className="h-full w-full " theme="light" editor={editor} />
  );
};

export default Documents;
