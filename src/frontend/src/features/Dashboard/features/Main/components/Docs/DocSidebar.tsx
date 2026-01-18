import { DocumentEditor } from "./DocumentEditor";
import type { DocumentData } from "@/services/documents";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { X, ChevronDown } from "lucide-react";

interface DocSidebarProps {
  documents: DocumentData[];
  selectedDocumentId: string | null;
  nodeId: string;
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
  onSelectDocument,
  onClose,
  onDocumentChange,
}: DocSidebarProps) {
  const selectedDocument = documents.find((d) => d._key === selectedDocumentId);

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header with Horizontal Doc list */}
      <div className="flex items-center border-b bg-background pr-2">
        <ScrollArea className="flex-1 whitespace-nowrap">
          <div className="flex p-1 gap-1">
            {documents.map((doc) => (
              <button
                key={doc._key}
                onClick={() => onSelectDocument(doc._key)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-md transition-all cursor-pointer whitespace-nowrap",
                  selectedDocumentId === doc._key
                    ? "bg-white border border-border shadow-sm font-semibold text-foreground ring-1 ring-black/5"
                    : "hover:bg-white/50 text-muted-foreground border border-transparent hover:text-foreground"
                )}
              >
                <span className="truncate max-w-[120px]">
                  {doc.name || "Untitled"}
                </span>
                {selectedDocumentId === doc._key && (
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
            className="p-1.5 hover:bg-white/50 rounded-md transition-colors text-muted-foreground hover:text-foreground ml-2 cursor-pointer"
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Editor below */}
      <div className="flex-1 overflow-hidden py-2">
        <DocumentEditor
          key={selectedDocument?._key || "new"}
          document={selectedDocument || null}
          nodeId={nodeId}
          autoSave={true}
          onChange={onDocumentChange}
          containerClassName="px-2 py-2"
        />
      </div>
    </div>
  );
}
