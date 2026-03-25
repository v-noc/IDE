import { DocumentEditor } from "./DocumentEditor";
import type { DocumentData } from "@/services/documents";

type DocumentsProps = {
  /**
   * Document to edit. Can be DocumentType or legacy format { id, data }.
   * If undefined, shows empty state.
   */
  document?: DocumentData | { id: string; data?: string; markdown?: string } | null;

  /**
   * Callback when document content changes.
   * Note: Auto-save is handled by DocumentEditor if nodeId is provided.
   */
  onChange?: (data: string) => void;

  /**
   * Node ID for API calls. Required for auto-save.
   */
  nodeId?: string;
};

/**
 * Documents Component (Legacy wrapper for DocumentEditor)
 *
 * This component maintains backward compatibility with the old API
 * while using the new DocumentEditor internally.
 *
 * @deprecated Consider using DocumentEditor directly for new code.
 */
const Documents = ({ document, onChange, nodeId }: DocumentsProps) => {
  const doc: DocumentData | null =
    !document
      ? null
      : "name" in document
        ? document
        : {
            id: document.id,
            name: "",
            description: "",
            data: document.data ?? "",
            markdown: "markdown" in document ? (document.markdown ?? "") : "",
            created_at: "",
            updated_at: "",
          };

  return (
    <DocumentEditor
      document={doc}
      nodeId={nodeId}
      autoSave={!!nodeId}
      onChange={onChange}
    />
  );
};

export default Documents;
