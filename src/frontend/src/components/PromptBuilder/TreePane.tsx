import React, { useMemo, useState } from "react";
import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronRight } from "lucide-react";
import type { AnyNodeTree, ContainerNodeTree } from "@/types/project";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import {
  canLazyLoadCodeChildren,
  useLazyCodeChildren,
} from "@/features/Dashboard/service/codeDescendants";
import { mergeStructureAndLazyChildren } from "@/features/Dashboard/utils/mergeCodeTreeChildren";
import { promptBuilderNodeKey } from "./nodeKey";
import {
  FileCode2,
  Folder,
  Box,
  FunctionSquare,
  Link2,
  Files,
  Library,
} from "lucide-react";

interface TreePaneProps {
  root: ContainerNodeTree;
  checked: Record<string, boolean>;
  selectedNodeKey: string | null;
  onToggleChecked: (key: string) => void;
  onSelect: (key: string) => void;
  onLazyParentAccordionChange?: (parentId: string, open: boolean) => void;
}

const getNodeIcon = (type: string) => {
  switch (type) {
    case "file":
      return FileCode2;
    case "folder":
      return Folder;
    case "project":
      return Library;
    case "function":
      return FunctionSquare;
    case "class":
      return Box;
    case "call":
      return Link2;
    case "group":
      return Files;
    default:
      return FileCode2;
  }
};

const treeCheckboxClass =
  "size-[15px] rounded border border-zinc-500 bg-transparent shadow-none data-[state=checked]:border-emerald-500 data-[state=checked]:bg-emerald-500 data-[state=checked]:text-zinc-950 dark:data-[state=checked]:bg-emerald-500";

const rowShellClass = (isSelected: boolean) =>
  cn(
    "group relative flex w-full items-center gap-2 rounded-md py-1.5 pl-1 pr-2 text-left transition-colors",
    "hover:bg-zinc-800/70",
    isSelected &&
      "bg-zinc-800/90 before:absolute before:left-0 before:top-1 before:bottom-1 before:w-[3px] before:rounded-sm before:bg-emerald-500",
  );

function nodeTypeBadge(nodeType: string) {
  const label = nodeType ? nodeType.replace(/_/g, " ") : "item";
  return (
    <span
      className="max-w-18 shrink-0 truncate rounded bg-zinc-800/90 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-zinc-400"
      title={label}
    >
      {label.length > 10 ? `${label.slice(0, 9)}…` : label}
    </span>
  );
}

interface PromptTreeNodeProps {
  node: ContainerNodeTree;
  checked: Record<string, boolean>;
  selectedNodeKey: string | null;
  onToggleChecked: (key: string) => void;
  onSelect: (key: string) => void;
  onLazyParentAccordionChange?: (parentId: string, open: boolean) => void;
}

const PromptTreeNode: React.FC<PromptTreeNodeProps> = ({
  node,
  checked,
  selectedNodeKey,
  onToggleChecked,
  onSelect,
  onLazyParentAccordionChange,
}) => {
  const key = promptBuilderNodeKey(node as AnyNodeTree);
  const [accordionValue, setAccordionValue] = useState<string[]>([]);
  const isOpen = accordionValue.includes(key);

  const lazy = useLazyCodeChildren(node, isOpen);

  const displayNode = useMemo((): ContainerNodeTree => {
    if (!lazy.loadedNodes.length) return node;
    return {
      ...node,
      children: mergeStructureAndLazyChildren(
        node.children,
        lazy.loadedNodes,
      ) as ContainerNodeTree["children"],
    };
  }, [node, lazy.loadedNodes]);

  const lazyHintCount = node.lazy_child_ids?.length ?? 0;
  const displayChildren = (displayNode.children ?? []) as ContainerNodeTree[];
  const hasChildren =
    displayChildren.length > 0 || lazyHintCount > 0 || lazy.isFetching;

  const isCall = node.node_type === "call";
  const targetNode = isCall
    ? (node as AnyNodeTree & { target?: AnyNodeTree }).target
    : null;
  const effectiveNode = (targetNode || node) as AnyNodeTree;
  const Icon = getNodeIcon(node.node_type);
  const subtitle =
    effectiveNode.description && String(effectiveNode.description).trim()
      ? String(effectiveNode.description).substring(0, 100)
      : (effectiveNode as { qname?: string }).qname;

  const isSelected = selectedNodeKey === key;
  const isChecked = !!checked[key];

  const checkboxEl = (
    <div
      className="flex shrink-0 items-center justify-center"
      onClick={(e) => e.stopPropagation()}
      onPointerDown={(e) => e.stopPropagation()}
    >
      <Checkbox
        className={treeCheckboxClass}
        checked={isChecked}
        onCheckedChange={() => {
          onToggleChecked(key);
        }}
        onClick={(e) => e.stopPropagation()}
      />
    </div>
  );

  const titleClass = cn(
    "truncate text-sm font-medium leading-tight",
    isSelected ? "text-cyan-300" : "text-zinc-100",
  );

  if (!hasChildren) {
    return (
      <li>
        <div
          role="treeitem"
          className={cn(
            rowShellClass(isSelected),
            "cursor-pointer py-2 pl-0.5",
          )}
          onClick={() => onSelect(key)}
        >
          <span className="inline-block w-5 shrink-0" aria-hidden />
          {checkboxEl}
          <Icon className="h-4 w-4 shrink-0 text-zinc-500" />
          <div className="flex min-w-0 flex-1 flex-col gap-0.5">
            <span className={titleClass}>{node.name}</span>
            {subtitle ? (
              <span className="truncate text-xs text-zinc-500">{subtitle}</span>
            ) : null}
          </div>
          {nodeTypeBadge(node.node_type)}
        </div>
      </li>
    );
  }

  return (
    <li>
      <AccordionPrimitive.Root
        type="multiple"
        value={accordionValue}
        onValueChange={(next) => {
          if (
            onLazyParentAccordionChange &&
            canLazyLoadCodeChildren(
              node as unknown as Parameters<typeof canLazyLoadCodeChildren>[0],
            )
          ) {
            const wasOpen = accordionValue.includes(key);
            const nowOpen = next.includes(key);
            if (wasOpen !== nowOpen) {
              onLazyParentAccordionChange(node.id, nowOpen);
            }
          }
          setAccordionValue(next);
        }}
      >
        <AccordionPrimitive.Item value={key}>
          <AccordionPrimitive.Header>
            <AccordionPrimitive.Trigger
              className={cn(
                "flex w-full flex-1 items-center gap-2 py-2 pl-0.5 text-left transition-all outline-none",
                "data-[state=open]:bg-zinc-900/50",
                rowShellClass(isSelected),
              )}
              onClick={() => onSelect(key)}
            >
              <span className="flex w-5 shrink-0 justify-center text-zinc-500">
                <ChevronRight
                  className={cn(
                    "h-4 w-4 transition-transform duration-200",
                    isOpen && "rotate-90",
                  )}
                />
              </span>
              {checkboxEl}
              <Icon className="h-4 w-4 shrink-0 text-zinc-500" />
              <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className={titleClass}>{node.name}</span>
                {subtitle ? (
                  <span className="truncate text-xs text-zinc-500">{subtitle}</span>
                ) : null}
              </div>
              {nodeTypeBadge(node.node_type)}
            </AccordionPrimitive.Trigger>
          </AccordionPrimitive.Header>
          <AccordionPrimitive.Content
            className={cn(
              "overflow-hidden text-sm transition-all data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down",
            )}
          >
            <div className="ml-2 border-l border-zinc-800 pb-1 pl-3 pt-0">
              <ul>
                {displayChildren.map((child) => (
                  <PromptTreeNode
                    key={promptBuilderNodeKey(child as AnyNodeTree)}
                    node={child as ContainerNodeTree}
                    checked={checked}
                    selectedNodeKey={selectedNodeKey}
                    onToggleChecked={onToggleChecked}
                    onSelect={onSelect}
                    onLazyParentAccordionChange={onLazyParentAccordionChange}
                  />
                ))}
              </ul>
            </div>
          </AccordionPrimitive.Content>
        </AccordionPrimitive.Item>
      </AccordionPrimitive.Root>
    </li>
  );
};

export const TreePane: React.FC<TreePaneProps> = ({
  root,
  checked,
  selectedNodeKey,
  onToggleChecked,
  onSelect,
  onLazyParentAccordionChange,
}) => {
  return (
    <div className="relative h-full overflow-y-auto overflow-x-hidden bg-zinc-950 p-2 text-zinc-100">
      <ul role="tree">
        <PromptTreeNode
          node={root}
          checked={checked}
          selectedNodeKey={selectedNodeKey}
          onToggleChecked={onToggleChecked}
          onSelect={onSelect}
          onLazyParentAccordionChange={onLazyParentAccordionChange}
        />
      </ul>
    </div>
  );
};

export default TreePane;
