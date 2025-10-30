import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { DynamicIcon } from "@/components/DynamicIcon";
import type { AnyNodeTree, GroupNodeTree, NodeType } from "@/types/project";
import { useMemo, useState } from "react";
import { useGroupUpdate } from "../service/useGroup";

type ChildCandidate = AnyNodeTree | GroupNodeTree;

interface ManageGroupsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  group: GroupNodeTree;
  siblings: AnyNodeTree[];
  project_key: string;
  onSave?: (data: {
    name: string;
    description: string;
    children_ids: string[];
  }) => void;
}

function NodeRow({
  node,
  checked,
  onCheckedChange,
}: {
  node: { _key: string; name: string; node_type: NodeType; icon?: string };
  checked: boolean;
  onCheckedChange: (next: boolean) => void;
}) {
  const iconName = node.icon;
  return (
    <div className="flex items-center gap-2 py-1 px-2 rounded-md hover:bg-muted/60">
      <Checkbox
        checked={checked}
        onCheckedChange={(v) => onCheckedChange(Boolean(v))}
      />
      <div className="flex items-center gap-2 min-w-0">
        <DynamicIcon iconName={iconName} className="h-4 w-4 shrink-0" />
        <div className="min-w-0">
          <div className="text-sm font-medium truncate">{node.name}</div>
          <div className="text-xs text-muted-foreground truncate">
            {node.node_type}
          </div>
        </div>
      </div>
      <div className="ml-auto">
        <Badge variant="secondary" className="text-xs capitalize">
          {node.node_type}
        </Badge>
      </div>
    </div>
  );
}

const ManageGroupsDialog = ({
  isOpen,
  onClose,
  group,
  siblings,
  project_key,
  onSave,
}: ManageGroupsDialogProps) => {
  const children = useMemo<ChildCandidate[]>(
    () => (group.children || []).slice() as ChildCandidate[],
    [group]
  );

  const [name, setName] = useState(group.name);
  const [description, setDescription] = useState(group.description || "");
  const [childrenSelected, setChildrenSelected] = useState<
    Record<string, boolean>
  >({});
  const [siblingsSelected, setSiblingsSelected] = useState<
    Record<string, boolean>
  >({});
  const [leftFilter, setLeftFilter] = useState("");
  const [rightFilter, setRightFilter] = useState("");
  const { addChildToGroupMutation, removeChildFromGroupMutation } =
    useGroupUpdate(group._key, project_key);

  const childKeys = useMemo(
    () => new Set(children.map((c) => c._key)),
    [children]
  );
  const availableSiblings = useMemo(
    () => siblings.filter((s) => !childKeys.has(s._key)),
    [siblings, childKeys]
  );

  const filteredChildren = useMemo(() => {
    if (!leftFilter) return children;
    const q = leftFilter.toLowerCase();
    return children.filter((c) => c.name.toLowerCase().includes(q));
  }, [children, leftFilter]);

  const filteredSiblings = useMemo(() => {
    if (!rightFilter) return availableSiblings;
    const q = rightFilter.toLowerCase();
    return availableSiblings.filter((c) => c.name.toLowerCase().includes(q));
  }, [availableSiblings, rightFilter]);

  const selectedSiblingIds = useMemo(
    () =>
      Object.entries(siblingsSelected)
        .filter(([, v]) => v)
        .map(([k]) => k),
    [siblingsSelected]
  );

  const selectedChildrenIds = useMemo(
    () =>
      Object.entries(childrenSelected)
        .filter(([, v]) => v)
        .map(([k]) => k),
    [childrenSelected]
  );

  const hasAddSelection = selectedSiblingIds.length > 0;
  const hasRemoveSelection = selectedChildrenIds.length > 0;
  const isMutating =
    addChildToGroupMutation.isPending || removeChildFromGroupMutation.isPending;

  const moveSelectedToChildren = async () => {
    if (!hasAddSelection) return;
    await Promise.all(
      selectedSiblingIds.map((id) => addChildToGroupMutation.mutateAsync(id))
    );
    setSiblingsSelected({});
  };

  const removeSelectedFromChildren = async () => {
    if (!hasRemoveSelection) return;
    await Promise.all(
      selectedChildrenIds.map((id) =>
        removeChildFromGroupMutation.mutateAsync(id)
      )
    );
    setChildrenSelected({});
  };

  const resetChanges = () => {
    setName(group.name);
    setDescription(group.description || "");
    setChildrenSelected({});
    setSiblingsSelected({});
    setLeftFilter("");
    setRightFilter("");
  };

  const handleSave = () => {
    const payload = {
      name: name.trim(),
      description: description.trim(),
      children_ids: children.map((c) => c._key),
    };
    onSave?.(payload);
    onClose();
  };

  const hasInfoChanges =
    name.trim() !== (group.name || "").trim() ||
    (description || "").trim() !== (group.description || "").trim();

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="w-full max-w-3xl sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Manage Group</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="group-name">Name</Label>
              <Input
                id="group-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter group name"
              />
            </div>
            <div className="space-y-2 col-span-2">
              <Label htmlFor="group-description">Description</Label>
              <Textarea
                id="group-description"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional description"
              />
            </div>
          </div>

          <Separator />

          <div className="grid grid-cols-2 gap-4 min-w-0">
            <div className="border rounded-md min-w-0">
              <div className="p-3 border-b">
                <div className="flex items-center justify-between gap-2">
                  <div className="font-medium">Children</div>
                  <Input
                    value={leftFilter}
                    onChange={(e) => setLeftFilter(e.target.value)}
                    placeholder="Filter..."
                    className="h-8 w-40"
                  />
                </div>
              </div>
              <ScrollArea className="h-64">
                <div className="p-2">
                  {filteredChildren.length === 0 ? (
                    <div className="text-sm text-muted-foreground px-2 py-8 text-center">
                      No children
                    </div>
                  ) : (
                    filteredChildren.map((node) => (
                      <NodeRow
                        key={node._key}
                        node={node}
                        checked={Boolean(childrenSelected[node._key])}
                        onCheckedChange={(next) =>
                          setChildrenSelected((prev) => ({
                            ...prev,
                            [node._key]: next,
                          }))
                        }
                      />
                    ))
                  )}
                </div>
              </ScrollArea>
            </div>

            <div className="border rounded-md min-w-0">
              <div className="p-3 border-b">
                <div className="flex items-center justify-between gap-2">
                  <div className="font-medium">Siblings</div>
                  <Input
                    value={rightFilter}
                    onChange={(e) => setRightFilter(e.target.value)}
                    placeholder="Filter..."
                    className="h-8 w-40"
                  />
                </div>
              </div>
              <ScrollArea className="h-64">
                <div className="p-2">
                  {filteredSiblings.length === 0 ? (
                    <div className="text-sm text-muted-foreground px-2 py-8 text-center">
                      No siblings available
                    </div>
                  ) : (
                    filteredSiblings.map((node) => (
                      <NodeRow
                        key={node._key}
                        node={node}
                        checked={Boolean(siblingsSelected[node._key])}
                        onCheckedChange={(next) =>
                          setSiblingsSelected((prev) => ({
                            ...prev,
                            [node._key]: next,
                          }))
                        }
                      />
                    ))
                  )}
                </div>
              </ScrollArea>
            </div>
          </div>

          <div className="flex items-center justify-between gap-2">
            <div className="flex gap-2">
              <Button
                variant="secondary"
                onClick={removeSelectedFromChildren}
                disabled={!hasRemoveSelection || isMutating}
              >
                Remove from children
              </Button>
              <Button
                onClick={moveSelectedToChildren}
                disabled={!hasAddSelection || isMutating}
              >
                Add to children
              </Button>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={resetChanges}>
                Reset
              </Button>
              <Button variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={!hasInfoChanges || !onSave}
              >
                Save
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ManageGroupsDialog;
