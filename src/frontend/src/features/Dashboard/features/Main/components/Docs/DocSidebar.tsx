import { DocumentEditor } from "./DocumentEditor";
import type { DocumentData } from "@/services/documents";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { X, ChevronDown } from "lucide-react";

interface DocSidebarProps {
  documents: DocumentData[];
  selectedDocumentId: string | null;
  nodeId: string;
  projectId: string;
  onSelectDocument: (id: string) => void;
  onClose?: () => void;
  /**
   * Optional callback when document content changes.
   * If not provided, DocumentEditor will handle auto-save internally.
   */
  onDocumentChange?: (data: string) => void;
}

/**
 * Document Sidebar Component
 *
 * A presentational component that displays a horizontal list of documents
 * and renders the DocumentEditor for the selected document.
 *
 * Responsibilities:
 * - Display document tabs
 * - Handle document selection
 * - Render DocumentEditor with selected document
 */
export function DocSidebar({
  documents,
  selectedDocumentId,
  nodeId,
  projectId,
  onSelectDocument,
  onClose,
  onDocumentChange,
}: DocSidebarProps) {
  const selectedDocument = documents.find((d) => d.id === selectedDocumentId);
  const getStatusClasses = (status?: DocumentData["status"]) => {
    if (status === "added") {
      return "border-emerald-600/90 bg-emerald-600 text-white hover:bg-emerald-700";
    }
    if (status === "removed") {
      return "border-rose-700/90 bg-rose-700 text-white opacity-60 hover:bg-rose-700";
    }
    return "";
  };

  return (
    <div className="flex flex-col h-full bg-(--background-color)">
      {/* Header with Horizontal Doc list */}
      <div className="flex items-center border-b bg-background pr-2">
        <ScrollArea className="flex-1 whitespace-nowrap">
          <div className="flex p-1 gap-1">
            {documents.map((doc) => (
              <button
                key={doc.id}
                onClick={() => onSelectDocument(doc.id)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-md transition-all cursor-pointer whitespace-nowrap",
                  getStatusClasses(doc.status),
                  selectedDocumentId === doc.id
                    ? "border shadow-sm font-semibold ring-1 ring-black/5"
                    : "border border-transparent",
                  (doc.status === "added" || doc.status === "removed")
                    ? ""
                    : selectedDocumentId === doc.id
                      ? "bg-card text-foreground"
                      : "hover:bg-muted/50 text-muted-foreground hover:text-foreground",
                )}
              >
                <span className="truncate max-w-[120px]">
                  {doc.name || "Untitled"}
                </span>
                {selectedDocumentId === doc.id && (
                  <ChevronDown className="h-3 w-3 opacity-50" />
                )}
              </button>
            ))}
          </div>
          <ScrollBar orientation="horizontal" className="hidden" />
        </ScrollArea>

        {onClose && (
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-muted/50 rounded-md transition-colors text-muted-foreground hover:text-foreground ml-2 cursor-pointer"
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Editor below */}
      <div className="flex-1 overflow-hidden py-2">
        <DocumentEditor
          key={selectedDocument?.id || "new"}
          document={selectedDocument || null}
          nodeId={nodeId}
          projectId={projectId}
          autoSave={true}
          onChange={onDocumentChange}
          containerClassName="px-2 py-2"
        />
      </div>
    </div>
  );
}
