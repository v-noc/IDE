import React, { useEffect } from "react";
import type { AnyNodeTree } from "@/types/project";
import { supportsCode } from "./types";
import { useDocuments } from "@/services/documents";
import { useCode } from "@/services/code";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SelectionDetailPaneProps {
  node: AnyNodeTree | null;
  checked: boolean;
  includeDocs: boolean;
  includeCode: boolean;
  onToggleDocs: () => void;
  onToggleCode: () => void;
  setDocumentsForNode: (key: string, docs: any[]) => void;
  setCodeForNode: (key: string, code: string) => void;
}

export const SelectionDetailPane: React.FC<SelectionDetailPaneProps> = ({
  node,
  checked,
  includeDocs,
  includeCode,
  onToggleDocs,
  onToggleCode,
  setDocumentsForNode,
  setCodeForNode,
}) => {
  const nodeId = node?._key ?? "";

  // Documents fetch when toggled on and node checked/selected
  const docsQuery = useDocuments(nodeId || undefined);
  useEffect(() => {
    if (node && checked && includeDocs && docsQuery.data) {
      setDocumentsForNode(node._key, docsQuery.data);
    }
  }, [node, checked, includeDocs, docsQuery.data, setDocumentsForNode]);

  // Code fetch when toggled on and supported type
  const codeQuery = useCode(nodeId || undefined, node?.node_type);
  useEffect(() => {
    if (node && checked && includeCode && codeQuery.data?.code) {
      setCodeForNode(node._key, codeQuery.data.code);
    }
  }, [node, checked, includeCode, codeQuery.data, setCodeForNode]);

  if (!node)
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Select a node to view details
      </div>
    );

  const canCode = supportsCode(node.node_type);

  return (
    <div className="space-y-4 h-full overflow-auto">
      {/* Options */}
      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <Switch
            id="include-docs"
            checked={!!includeDocs}
            onCheckedChange={onToggleDocs}
            disabled={!checked}
          />
          <Label
            htmlFor="include-docs"
            className="text-sm font-medium cursor-pointer"
          >
            Include Documents
          </Label>
        </div>
        {canCode && (
          <div className="flex items-center gap-3">
            <Switch
              id="include-code"
              checked={!!includeCode}
              onCheckedChange={onToggleCode}
              disabled={!checked}
            />
            <Label
              htmlFor="include-code"
              className="text-sm font-medium cursor-pointer"
            >
              Include Code
            </Label>
          </div>
        )}
      </div>

      <Separator />

      {/* Selected Node Info */}
      <div className="space-y-2">
        <div className="text-xs uppercase font-semibold text-muted-foreground">
          Selected Item
        </div>
        <div>
          <div className="inline-block px-2 py-1 rounded bg-muted text-xs font-mono uppercase mb-2">
            {node.node_type}
          </div>
          <div className="font-semibold text-sm">{node.name}</div>
          {node.description && (
            <div className="text-xs text-muted-foreground mt-1">
              {node.description}
            </div>
          )}
        </div>
      </div>

      {/* Documents Section */}
      {includeDocs && (
        <>
          <Separator />
          <div className="space-y-2">
            <div className="text-xs uppercase font-semibold text-muted-foreground">
              Documents
            </div>
            <div className="border rounded-md overflow-hidden bg-muted/20">
              {docsQuery.isLoading && (
                <div className="p-3 text-sm text-muted-foreground">
                  Loading documents…
                </div>
              )}
              {docsQuery.error && (
                <div className="p-3 text-sm text-destructive">
                  Failed to load documents
                </div>
              )}
              {docsQuery.data && docsQuery.data.length === 0 && (
                <div className="p-3 text-sm text-muted-foreground">
                  No documents
                </div>
              )}
              {docsQuery.data && docsQuery.data.length > 0 && (
                <ScrollArea className="h-48">
                  <div className="space-y-3 p-3">
                    {docsQuery.data.map((d) => (
                      <div
                        key={d._key}
                        className="border rounded p-2 bg-background text-xs space-y-1"
                      >
                        <div className="font-semibold">{d.name}</div>
                        {d.description && (
                          <div className="text-muted-foreground line-clamp-1">
                            {d.description}
                          </div>
                        )}
                        <div className="whitespace-pre-wrap text-xs bg-muted/30 rounded p-1 max-h-20 overflow-auto">
                          {d.data}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </div>
          </div>
        </>
      )}

      {/* Code Section */}
      {canCode && includeCode && (
        <>
          <Separator />
          <div className="space-y-2">
            <div className="text-xs uppercase font-semibold text-muted-foreground">
              Code
            </div>
            <div className="border rounded-md overflow-hidden bg-muted/20">
              {codeQuery.isLoading && (
                <div className="p-3 text-sm text-muted-foreground">
                  Loading code…
                </div>
              )}
              {codeQuery.error && (
                <div className="p-3 text-sm text-destructive">
                  Failed to load code
                </div>
              )}
              {codeQuery.data?.code && (
                <ScrollArea className="h-48">
                  <pre className="text-xs bg-muted/30 p-3 font-mono whitespace-pre-wrap break-words">
                    {codeQuery.data.code}
                  </pre>
                </ScrollArea>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SelectionDetailPane;
