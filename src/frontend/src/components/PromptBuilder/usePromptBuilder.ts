import { useCallback, useState } from "react";
import type { AnyNodeTree, ContainerNodeTree } from "@/types/project";
import type { DocumentData } from "@/services/documents";
import { supportsCode } from "./types";

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
}

export const usePromptBuilder = (rootNode: ContainerNodeTree): UsePromptBuilderState => {
  const [checked, setChecked] = useState<Record<string, boolean>>({ [rootNode._key]: true });
  const [includeDocs, setIncludeDocs] = useState<Record<string, boolean>>({});
  const [includeCode, setIncludeCode] = useState<Record<string, boolean>>({});
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ [rootNode._key]: true });
  const [selectedNodeKey, setSelectedNodeKey] = useState<string | null>(rootNode._key);
  const [documentsByNode, setDocumentsByNode] = useState<Record<string, DocumentData[]>>({});
  const [codeByNode, setCodeByNode] = useState<Record<string, string>>({});

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

  const findNodeByKey = useCallback((key: string, node: AnyNodeTree): AnyNodeTree | null => {
    if (node._key === key) return node;
    for (const child of (node.children ?? []) as AnyNodeTree[]) {
      const found = findNodeByKey(key, child);
      if (found) return found;
    }
    return null;
  }, []);

  const escapeAttr = (s: string | undefined) => (s ?? "").replace(/"/g, "&quot;");
  const wrapCdata = (text: string) => `<![CDATA[${text ?? ""}]]>`;

  const buildXml = useCallback((node: AnyNodeTree): string => {
    if (!checked[node._key]) return "";
    const attrs: string[] = [
      `name="${escapeAttr(node.name)}"`,
    ];
    if (node.description) attrs.push(`description="${escapeAttr(node.description)}"`);
    if (node.node_type === "group" && node.group_type) attrs.push(`group_type="${escapeAttr(node.group_type)}"`);

    const children = (node.children ?? []) as AnyNodeTree[];
    const childrenXml = children.map(buildXml).filter(Boolean).join("");

    const parts: string[] = [];
    // documents
    if (includeDocs[node._key]) {
      const docs = documentsByNode[node._key] ?? [];
      const docsXml = docs.map(d => `<doc name="${escapeAttr(d.name)}">${wrapCdata(d.data)}</doc>`).join("");
      parts.push(`<documents>${docsXml}</documents>`);
    }
    // code
    if (includeCode[node._key] && supportsCode(node.node_type)) {
      const code = codeByNode[node._key] ?? "";
      parts.push(`<code>${wrapCdata(code)}</code>`);
    }

    return `<${node.node_type} ${attrs.join(" ")}>${parts.join("")}${childrenXml}</${node.node_type}>`;
  }, [checked, includeDocs, includeCode, documentsByNode, codeByNode]);

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
  };
};


