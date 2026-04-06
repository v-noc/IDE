import { useCallback, useMemo, useState } from "react";
import { useQueries } from "@tanstack/react-query";
import type { AnyNodeTree, ContainerNodeTree } from "@/types/project";
import type { DocumentData } from "@/services/documents";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import {
  canLazyLoadCodeChildren,
  getCodeDescendantsQueryOptions,
} from "@/features/Dashboard/service/codeDescendants";
import { mergeStructureAndLazyChildren } from "@/features/Dashboard/utils/mergeCodeTreeChildren";
import { supportsCode } from "./types";
import { promptBuilderNodeKey } from "./nodeKey";

export interface UsePromptBuilderState {
  checked: Record<string, boolean>;
  includeDocs: Record<string, boolean>;
  includeCode: Record<string, boolean>;
  expanded: Record<string, boolean>;
  selectedNodeKey: string | null;
  setSelectedNodeKey: (key: string | null) => void;
  toggleChecked: (key: string) => void;
  toggleIncludeDocs: (key: string) => void;
  toggleIncludeCode: (key: string) => void;
  toggleExpanded: (key: string) => void;
  setDocumentsForNode: (key: string, docs: DocumentData[]) => void;
  setCodeForNode: (key: string, code: string) => void;
  generateXml: () => string;
  /** Call when a lazy-code parent’s accordion opens (same query keys as `useLazyCodeChildren`; stays subscribed after first open). */
  onLazyParentAccordionChange: (parentId: string, open: boolean) => void;
}

export const usePromptBuilder = (rootNode: ContainerNodeTree): UsePromptBuilderState => {
  const rootKey = promptBuilderNodeKey(rootNode as AnyNodeTree);
  const [checked, setChecked] = useState<Record<string, boolean>>({ [rootKey]: true });
  const [includeDocs, setIncludeDocs] = useState<Record<string, boolean>>({});
  const [includeCode, setIncludeCode] = useState<Record<string, boolean>>({});
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ [rootKey]: true });
  const [selectedNodeKey, setSelectedNodeKey] = useState<string | null>(rootKey);
  const [documentsByNode, setDocumentsByNode] = useState<Record<string, DocumentData[]>>({});
  const [codeByNode, setCodeByNode] = useState<Record<string, string>>({});
  const [openLazyParentIds, setOpenLazyParentIds] = useState<string[]>([]);

  const projectKey = useProjectStore((s) => s.projectData?.id ?? "");
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);

  const onLazyParentAccordionChange = useCallback((parentId: string, open: boolean) => {
    if (!parentId || !open) return;
    setOpenLazyParentIds((prev) => {
      if (prev.includes(parentId)) return prev;
      return [...prev, parentId].sort();
    });
  }, []);

  const descendantQueries = useQueries({
    queries: openLazyParentIds.map((parentId) => ({
      ...getCodeDescendantsQueryOptions(projectKey, parentId, branch, ref, compareTo),
      enabled: !!projectKey && !!parentId,
    })),
  });

  const lazyChildrenByParentId = useMemo(() => {
    const m = new Map<string, AnyNodeTree[]>();
    openLazyParentIds.forEach((parentId, i) => {
      const roots = descendantQueries[i]?.data?.children;
      if (roots?.length) {
        m.set(parentId, roots as unknown as AnyNodeTree[]);
      }
    });
    return m;
  }, [openLazyParentIds, descendantQueries]);

  const toggle = (mapSetter: React.Dispatch<React.SetStateAction<Record<string, boolean>>>) =>
    (key: string) => mapSetter(prev => ({ ...prev, [key]: !prev[key] }));

  const toggleChecked = toggle(setChecked);
  const toggleIncludeDocs = toggle(setIncludeDocs);
  const toggleIncludeCode = toggle(setIncludeCode);
  const toggleExpanded = toggle(setExpanded);

  const setDocumentsForNode = useCallback((key: string, docs: DocumentData[]) => {
    setDocumentsByNode(prev => ({ ...prev, [key]: docs }));
  }, []);

  const setCodeForNode = useCallback((key: string, code: string) => {
    setCodeByNode(prev => ({ ...prev, [key]: code }));
  }, []);

  const getMergedChildren = useCallback(
    (node: AnyNodeTree): AnyNodeTree[] => {
      const structure = ((node as ContainerNodeTree).children ?? []) as AnyNodeTree[];
      if (
        !projectKey ||
        !canLazyLoadCodeChildren(
          node as unknown as Parameters<typeof canLazyLoadCodeChildren>[0],
        )
      ) {
        return structure;
      }
      const loaded = lazyChildrenByParentId.get(node.id) ?? [];
      return mergeStructureAndLazyChildren(structure, loaded);
    },
    [projectKey, lazyChildrenByParentId],
  );

  const escapeAttr = (s: string | undefined) => (s ?? "").replace(/"/g, "&quot;");
  const wrapCdata = (text: string) => `<![CDATA[${text ?? ""}]]>`;

  const buildXml = useCallback((node: AnyNodeTree): string => {
    const nk = promptBuilderNodeKey(node);
    if (!checked[nk]) return "";

    const isCall = node.node_type === "call";
    const targetNode = isCall ? (node as AnyNodeTree & { target?: AnyNodeTree }).target : null;
    const effectiveNode = targetNode || node;
    const nodeType = effectiveNode.node_type;

    const attrs: string[] = [
      `name="${escapeAttr(effectiveNode.name)}"`,
    ];
    if (effectiveNode.description) attrs.push(`description="${escapeAttr(effectiveNode.description)}"`);
    if (effectiveNode.node_type === "group" && (effectiveNode as AnyNodeTree & { group_type?: string }).group_type) {
      attrs.push(`group_type="${escapeAttr((effectiveNode as AnyNodeTree & { group_type?: string }).group_type)}"`);
    }
    const qn = (effectiveNode as AnyNodeTree & { qname?: string }).qname;
    if (qn) {
      attrs.push(`qname="${escapeAttr(qn)}"`);
    }

    const children = getMergedChildren(node);
    const childrenXml = children.map(buildXml).filter(Boolean).join("");

    const parts: string[] = [];
    if (includeDocs[nk]) {
      const docs = documentsByNode[nk] ?? [];
      const docsXml = docs.map(d => `<doc name="${escapeAttr(d.name)}">${wrapCdata(d.data)}</doc>`).join("");
      parts.push(`<documents>${docsXml}</documents>`);
    }
    if (includeCode[nk] && supportsCode(nodeType)) {
      const code = codeByNode[nk] ?? "";
      parts.push(`<code>${wrapCdata(code)}</code>`);
    }

    return `<${nodeType} ${attrs.join(" ")}>${parts.join("")}${childrenXml}</${nodeType}>`;
  }, [checked, includeDocs, includeCode, documentsByNode, codeByNode, getMergedChildren]);

  const generateXml = useCallback(() => {
    return buildXml(rootNode as AnyNodeTree);
  }, [buildXml, rootNode]);

  return {
    checked,
    includeDocs,
    includeCode,
    expanded,
    selectedNodeKey,
    setSelectedNodeKey,
    toggleChecked,
    toggleIncludeDocs,
    toggleIncludeCode,
    toggleExpanded,
    setDocumentsForNode,
    setCodeForNode,
    generateXml,
    onLazyParentAccordionChange,
  };
};
