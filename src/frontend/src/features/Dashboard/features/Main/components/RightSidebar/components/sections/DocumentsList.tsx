import React, { useMemo, useState } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import {
  useGetDocuments,
  useCreateDocument,
  useUpdateDocument,
  useDeleteDocument,
  type DocumentType,
} from "@/features/Dashboard/features/Main/service/useDocuments";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from "@/components/ui/dialog";
import { Plus, Pencil, Trash2, FileText } from "lucide-react";
import type { CallNodeTree } from "@/types/project";

const DocumentsList: React.FC = () => {
  const activeTabId = useTabStore((s) => s.activeTabId);
  const selectedNode = useProjectStore((s) => s.selectedNode[activeTabId]);
  const secondarySelectedNode = useProjectStore((s) => s.secondarySelectedNode[activeTabId]);
  const selectedDocumentId = useProjectStore((s) => s.selectedDocumentId[activeTabId]);
  const setSelectedDocumentId = useProjectStore((s) => s.setSelectedDocumentId);
  const nodeKey = useMemo(() => {
    if (secondarySelectedNode) {
      return (secondarySelectedNode as CallNodeTree).target
        ? (secondarySelectedNode as CallNodeTree)?.target?._key ?? ""
        : secondarySelectedNode._key;
    }
    return selectedNode?._key;
  }, [selectedNode, secondarySelectedNode]);
  const queryClient = useQueryClient();

  const { data: docs = [], isLoading } = useGetDocuments(nodeKey ?? "");
  const createMutation = useCreateDocument();
  const updateMutation = useUpdateDocument(nodeKey ?? "");
  const deleteMutation = useDeleteDocument();

  const [formName, setFormName] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  // Listen for external document selections to keep highlight in sync

  const canUseDocs = useMemo(() => Boolean(nodeKey), [nodeKey]);

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["documents", nodeKey] });

  const openCreateDialog = () => {
    setEditingId(null);
    setFormName("");
    setFormDesc("");
    setOpen(true);
  };

  const startEdit = (doc: DocumentType) => {
    setEditingId(doc._key);
    setFormName(doc.name);
    setFormDesc(doc.description);
    setOpen(true);
  };

  const onSubmitDialog = async () => {
    if (!formName.trim() || !formDesc.trim()) return;
    if (editingId) {
      await updateMutation.mutateAsync({
        id: editingId,
        name: formName.trim(),
        description: formDesc.trim(),
      });
    } else {
      if (!canUseDocs) return;
      await createMutation.mutateAsync({
        name: formName.trim(),
        description: formDesc.trim(),
        node_id: nodeKey ?? "",
      });
    }
    setOpen(false);
    setEditingId(null);
    refresh();
  };

  const onDelete = async (doc: DocumentType) => {
    if (!canUseDocs) return;
    await deleteMutation.mutateAsync({
      documentId: doc._key,
      nodeId: nodeKey ?? "",
    });
    refresh();
  };

  if (!selectedNode) {
    return (
      <div className="text-sm text-muted-foreground">
        Select a node to manage documents.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-xs font-semibold text-muted-foreground">
          Documents
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm" disabled={!canUseDocs} onClick={openCreateDialog}>
              <Plus className="h-4 w-4" />
              <span className="sr-only">New document</span>
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingId ? "Edit Document" : "New Document"}
              </DialogTitle>
              <DialogDescription>
                {editingId
                  ? "Update document details."
                  : "Create a document under the selected node."}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2 py-2">
              <Input
                placeholder="Name"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
              />
              <Textarea
                placeholder="Description"
                value={formDesc}
                onChange={(e) => setFormDesc(e.target.value)}
                rows={3}
              />
            </div>
            <DialogFooter>
              <Button
                size="sm"
                onClick={onSubmitDialog}
                disabled={!formName.trim() || (!editingId && !canUseDocs)}
              >
                {editingId ? "Save" : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="space-y-2">
        {isLoading ? (
          <div className="text-xs text-muted-foreground">Loading...</div>
        ) : docs.length === 0 ? (
          <div className="flex items-center justify-center py-10">
            <div className="text-center">
              <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full border bg-background">
                <FileText className="h-5 w-5 text-muted-foreground" />
              </div>
              <div className="text-sm font-medium">No documents yet</div>
              <div className="text-xs text-muted-foreground mb-3">
                Create your first document to get started.
              </div>
              <Button
                size="sm"
                onClick={openCreateDialog}
                disabled={!canUseDocs}
              >
                <Plus className="h-4 w-4 mr-1" /> Create Document
              </Button>
            </div>
          </div>
        ) : (
          docs.map((doc) => (
            <Card
              key={doc._key}
              className={
                "p-3 shadow-none rounded-sm hover:cursor-pointer transition " +
                (selectedDocumentId === doc._key
                  ? "ring-2 ring-primary ring-offset-1"
                  : "")
              }
              onClick={() => {

                setSelectedDocumentId(activeTabId, doc._key);
                useProjectStore.getState().setDocSidebarOpen(activeTabId, true);
              }}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-sm font-medium">{doc.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {doc.description}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      startEdit(doc);
                    }}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(doc);
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default DocumentsList;
