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

const treeRowClass =
  "group hover:before:opacity-100 before:absolute before:rounded-lg before:left-0 px-2 before:w-full before:opacity-0 before:bg-accent/70 before:h-[2rem] before:-z-10";

const selectedRowClass =
  "before:opacity-100 before:bg-accent/70 text-accent-foreground";

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
  const targetNode = isCall ? (node as AnyNodeTree & { target?: AnyNodeTree }).target : null;
  const effectiveNode = (targetNode || node) as AnyNodeTree;
  const Icon = getNodeIcon(node.node_type);
  const subtitle =
    effectiveNode.description && String(effectiveNode.description).trim()
      ? String(effectiveNode.description).substring(0, 100)
      : (effectiveNode as { qname?: string }).qname;

  const isSelected = selectedNodeKey === key;

  const checkbox = (
    <Checkbox
      checked={!!checked[key]}
      onCheckedChange={() => {
        onToggleChecked(key);
      }}
      onClick={(e) => e.stopPropagation()}
    />
  );

  if (!hasChildren) {
    return (
      <li>
        <div
          role="treeitem"
          className={cn(
            "ml-5 flex text-left items-center py-2 cursor-pointer before:right-1 relative",
            treeRowClass,
            isSelected && selectedRowClass,
          )}
          onClick={() => onSelect(key)}
        >
          <Icon className="h-4 w-4 shrink-0 mr-2" />
          <div className="flex flex-col grow min-w-0">
            <span className="text-sm truncate">{node.name}</span>
            {subtitle ? (
              <span className="text-xs text-muted-foreground truncate">
                {subtitle}
              </span>
            ) : null}
          </div>
          <div
            className={cn(
              isSelected ? "block" : "hidden",
              "absolute right-3 group-hover:block",
            )}
          >
            {checkbox}
          </div>
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
                "flex flex-1 w-full items-center py-2 transition-all relative text-left",
                "first:[&[data-state=open]>svg]:first-of-type:rotate-90",
                treeRowClass,
                isSelected && selectedRowClass,
              )}
              onClick={() => onSelect(key)}
            >
              <ChevronRight className="h-4 w-4 shrink-0 transition-transform duration-200 text-accent-foreground/50 mr-1" />
              <Icon className="h-4 w-4 shrink-0 mr-2" />
              <div className="flex flex-col min-w-0 flex-1">
                <span className="text-sm truncate">{node.name}</span>
                {subtitle ? (
                  <span className="text-xs text-muted-foreground truncate">
                    {subtitle}
                  </span>
                ) : null}
              </div>
              <div
                className={cn(
                  isSelected ? "block" : "hidden",
                  "absolute right-3 group-hover:block",
                )}
                onClick={(e) => e.stopPropagation()}
              >
                {checkbox}
              </div>
            </AccordionPrimitive.Trigger>
          </AccordionPrimitive.Header>
          <AccordionPrimitive.Content
            className={cn(
              "overflow-hidden text-sm transition-all data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down",
            )}
          >
            <div className="pb-1 pt-0 ml-4 pl-1 border-l">
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
    <div className="overflow-hidden relative p-2 h-full overflow-y-auto">
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
