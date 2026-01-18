
import Documents from "./index";
import type { DocumentType } from "../../service/useDocuments";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

interface DocSidebarProps {
    documents: DocumentType[];
    selectedDocumentId: string | null;
    onDocumentChange: (data: string) => void;
    onSelectDocument: (id: string) => void;
}

export function DocSidebar({
    documents,
    selectedDocumentId,
    onDocumentChange,
    onSelectDocument,
}: DocSidebarProps) {
    const selectedDocument = documents.find((d) => d._key === selectedDocumentId);

    return (
        <div className="flex flex-col h-full bg-white">
            {/* Doc list on top */}
            <div className="p-3 border-b bg-(--background-color)">
                <h3 className="text-sm font-semibold mb-2 px-1 text-muted-foreground">Documents</h3>
                <ScrollArea className="h-40">
                    <div className="space-y-1">
                        {documents.map((doc) => (
                            <button
                                key={doc._key}
                                onClick={() => onSelectDocument(doc._key)}
                                className={cn(
                                    "w-full text-left px-2 py-1.5 text-xs rounded-md transition-colors cursor-pointer",
                                    selectedDocumentId === doc._key
                                        ? "bg-white border border-border shadow-sm font-semibold"
                                        : "hover:bg-white/50 text-muted-foreground border border-transparent"
                                )}
                            >
                                {doc.name || "Untitled Document"}
                            </button>
                        ))}
                        {documents.length === 0 && (
                            <div className="text-xs text-muted-foreground px-2 py-1">
                                No documents available
                            </div>
                        )}
                    </div>
                </ScrollArea>
            </div>

            {/* Editor below */}
            <div className="flex-1 overflow-hidden">
                <Documents
                    key={selectedDocument?._key || "new"}
                    document={
                        selectedDocument
                            ? {
                                id: selectedDocument._key,
                                data: selectedDocument.data,
                            }
                            : undefined
                    }
                    onChange={onDocumentChange}
                />
            </div>
        </div>
    );
}
