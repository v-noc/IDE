import React, { useEffect } from "react";
import type { AnyNodeTree } from "@/types/project";
import { supportsCode } from "./types";
import { promptBuilderNodeKey } from "./nodeKey";
import { useDocuments } from "@/services/documents";
import { useCode } from "@/services/code";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Link2, FileText, Code2, AlertCircle } from "lucide-react";

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
  const isCall = node?.node_type === "call";
  const targetNode = isCall ? (node as any).target : null;
  const effectiveNode = targetNode || node;
  const effectiveNodeId = effectiveNode
    ? promptBuilderNodeKey(effectiveNode)
    : "";
  const effectiveNodeType = effectiveNode?.node_type;
  const projectId = useProjectStore((s) => s.projectData?.id);

  // Documents fetch when toggled on and node checked/selected
  const docsQuery = useDocuments(
    effectiveNodeId || undefined,
    projectId || undefined,
  );
  useEffect(() => {
    if (effectiveNode && node && checked && includeDocs && docsQuery.data) {
      setDocumentsForNode(promptBuilderNodeKey(node), docsQuery.data);
    }
  }, [
    effectiveNode,
    node,
    checked,
    includeDocs,
    docsQuery.data,
    setDocumentsForNode,
  ]);

  // Code fetch when toggled on and supported type
  const codeQuery = useCode(
    effectiveNodeId || undefined,
    effectiveNodeType,
    projectId || undefined,
  );
  useEffect(() => {
    if (
      effectiveNode &&
      node &&
      checked &&
      includeCode &&
      codeQuery.data?.code
    ) {
      setCodeForNode(promptBuilderNodeKey(node), codeQuery.data.code);
    }
  }, [effectiveNode, node, checked, includeCode, codeQuery.data]);

  if (!node)
    return (
      <div className="flex flex-col items-center justify-center h-full text-sm text-muted-foreground bg-muted/5 rounded-lg border-2 border-dashed">
        <div className="mb-2">{/* Could add a selection icon here */}</div>
        Select a node to view details
      </div>
    );

  const canCode = supportsCode(effectiveNodeType);

  return (
    <div className="space-y-6 h-full p-1 overflow-auto scrollbar-hide">
      {/* Options Card */}
      <div className="p-4 rounded-xl bg-card border shadow-sm space-y-4">
        <div className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground/70 mb-2">
          Selection Options
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label
              htmlFor="include-docs"
              className="text-sm font-medium cursor-pointer"
            >
              Include Documents
            </Label>
            <Switch
              id="include-docs"
              checked={!!includeDocs}
              onCheckedChange={onToggleDocs}
              disabled={!checked}
            />
          </div>
          {canCode && (
            <div className="flex items-center justify-between">
              <Label
                htmlFor="include-code"
                className="text-sm font-medium cursor-pointer"
              >
                Include Code
              </Label>
              <Switch
                id="include-code"
                checked={!!includeCode}
                onCheckedChange={onToggleCode}
                disabled={!checked}
              />
            </div>
          )}
        </div>
      </div>

      {/* Selected Node Info Card */}
      <div className="p-4 rounded-xl bg-card border shadow-sm space-y-3 relative overflow-hidden">
        <div className="flex items-center justify-between">
          <div className="text-[10px] uppercase font-bold tracking-wider text-muted-foreground/70">
            Selected Item
          </div>
          <div className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-wider">
            {node.node_type}
          </div>
        </div>

        <div className="space-y-1">
          <div className="flex items-center flex-wrap gap-2">
            <h3 className="font-bold text-base tracking-tight">
              {effectiveNode.name}
            </h3>
            {isCall && targetNode && (
              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 text-[10px] font-semibold border border-amber-500/20">
                <Link2 className="w-3 h-3" />
                <span>Redirected from: {node.name}</span>
              </div>
            )}
          </div>
          {effectiveNode.qname && (
            <div className="text-[11px] font-mono text-muted-foreground/80 break-all leading-relaxed">
              {effectiveNode.qname}
            </div>
          )}
        </div>

        {effectiveNode.description && (
          <div className="text-sm text-muted-foreground leading-relaxed bg-muted/30 p-3 rounded-lg border border-muted/50">
            {effectiveNode.description}
          </div>
        )}
      </div>

      {/* Documents Section */}
      {includeDocs && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-[10px] uppercase font-bold tracking-wider text-muted-foreground/70 px-1">
            <FileText className="w-3.5 h-3.5" />
            Documents
          </div>
          <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
            {docsQuery.isLoading && (
              <div className="p-8 text-center space-y-2">
                <div className="animate-spin inline-block w-4 h-4 border-2 border-primary border-t-transparent rounded-full" />
                <div className="text-xs text-muted-foreground">
                  Loading documents…
                </div>
              </div>
            )}
            {docsQuery.error && (
              <div className="p-6 text-center text-destructive flex flex-col items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                <div className="text-xs font-medium">
                  Failed to load documents
                </div>
              </div>
            )}
            {docsQuery.data && docsQuery.data.length === 0 && (
              <div className="p-8 text-center text-xs text-muted-foreground/60 italic">
                No documents available for this node
              </div>
            )}
            {docsQuery.data && docsQuery.data.length > 0 && (
              <ScrollArea className="h-64">
                <div className="divide-y divide-border">
                  {docsQuery.data.map((d) => (
                    <div
                      key={d.id}
                      className="p-4 hover:bg-muted/30 transition-colors space-y-2"
                    >
                      <div className="font-semibold text-xs flex items-center gap-2">
                        <div className="w-1 h-3 bg-primary/40 rounded-full" />
                        {d.name}
                      </div>
                      {d.description && (
                        <div className="text-[11px] text-muted-foreground leading-snug italic">
                          {d.description}
                        </div>
                      )}
                      <div className="whitespace-pre-wrap text-[11px] font-mono bg-muted/50 rounded-lg p-3 border border-muted/30 max-h-32 overflow-auto scrollbar-hide">
                        {d.data}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </div>
        </div>
      )}

      {/* Code Section */}
      {canCode && includeCode && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-[10px] uppercase font-bold tracking-wider text-muted-foreground/70 px-1">
            <Code2 className="w-3.5 h-3.5" />
            Source Code
          </div>
          <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
            {codeQuery.isLoading && (
              <div className="p-8 text-center space-y-2">
                <div className="animate-spin inline-block w-4 h-4 border-2 border-primary border-t-transparent rounded-full" />
                <div className="text-xs text-muted-foreground">
                  Loading code…
                </div>
              </div>
            )}
            {codeQuery.error && (
              <div className="p-6 text-center text-destructive flex flex-col items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                <div className="text-xs font-medium">Failed to load code</div>
              </div>
            )}
            {codeQuery.data?.code && (
              <ScrollArea className="h-80">
                <div className="relative">
                  <pre className="text-[11px] bg-muted/20 p-4 font-mono whitespace-pre-wrap break-words leading-relaxed">
                    {codeQuery.data.code}
                  </pre>
                  <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {/* Copy button could go here */}
                  </div>
                </div>
              </ScrollArea>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SelectionDetailPane;
