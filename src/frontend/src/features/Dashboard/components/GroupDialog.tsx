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
import { useMemo, useState, useEffect, useEffectEvent } from "react";
import { useCreateGroup, useUpdateGroup, useGroupUpdate } from "../service/useGroup";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

type ChildCandidate = AnyNodeTree;

interface GroupDialogProps {
    isOpen: boolean;
    onClose: () => void;
    mode: "create" | "manage";
    // For Create mode
    initialChildren?: AnyNodeTree[];
    parent_node_id?: string;
    // For Manage mode
    group?: GroupNodeTree;
    siblings?: AnyNodeTree[];
    project_key: string;
}

const formSchema = z.object({
    name: z.string().min(1, "Name is required").max(100),
    description: z.string().max(500),
});

type GroupFormValues = z.infer<typeof formSchema>;

function NodeRow({
    node,
    checked,
    onCheckedChange,
}: {
    node: { _key: string; name: string; node_type: NodeType; icon?: string };
    checked: boolean;
    onCheckedChange: (next: boolean) => void;
}) {
    return (
        <div className="flex items-center gap-2 py-1 px-2 rounded-md hover:bg-muted/60">
            <Checkbox
                checked={checked}
                onCheckedChange={(v) => onCheckedChange(Boolean(v))}
            />
            <div className="flex items-center gap-2 min-w-0">
                <DynamicIcon iconName={node.icon} className="h-4 w-4 shrink-0" />
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

const GroupDialog = ({
    isOpen,
    onClose,
    mode,
    initialChildren = [],
    parent_node_id,
    group,
    siblings = [],
    project_key,
}: GroupDialogProps) => {
    const isCreate = mode === "create";
    const title = isCreate ? "Create Group" : "Manage Group";

    const { mutate: createGroup, isPending: isCreating } = useCreateGroup(
        parent_node_id || "",
        project_key
    );
    const { mutate: updateGroup, isPending: isUpdating } = useUpdateGroup(
        group?._key || "",
        project_key
    );
    const { addChildToGroupMutation, removeChildFromGroupMutation } = useGroupUpdate(
        group?._key || "",
        project_key
    );

    const form = useForm<GroupFormValues>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            name: group?.name || "",
            description: group?.description || "",
        },
    });

    // Local state for children selection in CREATE mode OR incremental selection in MANAGE mode
    const [currentChildren, setCurrentChildren] = useState<ChildCandidate[]>([]);
    const [childrenSelected, setChildrenSelected] = useState<Record<string, boolean>>({});
    const [siblingsSelected, setSiblingsSelected] = useState<Record<string, boolean>>({});
    const [leftFilter, setLeftFilter] = useState("");
    const [rightFilter, setRightFilter] = useState("");

    // 1. THE "WHAT": The Effect Event (Non-Reactive)
    // This function always sees the latest props/state but DOES NOT trigger re-runs.
    const onDialogInit = useEffectEvent((isCreate: boolean, group: any) => {
        if (isCreate) {
            setCurrentChildren(initialChildren);
            form.reset({ name: "", description: "" });
        } else if (group) {
            setCurrentChildren((group.children || []) as ChildCandidate[]);
            form.reset({ name: group.name, description: group.description || "" });
        }
        
        // Clear filters and selections
        setChildrenSelected({});
        setSiblingsSelected({});
        setLeftFilter("");
        setRightFilter("");
    });
    
    // 2. THE "WHEN": The Effect (Reactive)
    // This only triggers when the fundamental "source of truth" changes.
    useEffect(() => {
        if (isOpen) {
            // We call the event here. 
            // We don't need 'form' or 'initialChildren' in the dependency array anymore!
            onDialogInit(isCreate, group);
        }
    }, [isOpen, isCreate, group?._key]); // Only react to the ID, not the whole object

    const availableSiblings = useMemo(() => {
        const childKeys = new Set(currentChildren.map((c) => c._key));
        return siblings.filter((s) => !childKeys.has(s._key) && s._key !== group?._key);
    }, [siblings, currentChildren, group?._key]);

    const filteredChildren = useMemo(() => {
        if (!leftFilter) return currentChildren;
        const q = leftFilter.toLowerCase();
        return currentChildren.filter((c) => c.name.toLowerCase().includes(q));
    }, [currentChildren, leftFilter]);

    const filteredSiblings = useMemo(() => {
        if (!rightFilter) return availableSiblings;
        const q = rightFilter.toLowerCase();
        return availableSiblings.filter((c) => c.name.toLowerCase().includes(q));
    }, [availableSiblings, rightFilter]);

    const selectedSiblingIds = useMemo(
        () => Object.entries(siblingsSelected).filter(([, v]) => v).map(([k]) => k),
        [siblingsSelected]
    );

    const selectedChildrenIds = useMemo(
        () => Object.entries(childrenSelected).filter(([, v]) => v).map(([k]) => k),
        [childrenSelected]
    );

    const hasAddSelection = selectedSiblingIds.length > 0;
    const hasRemoveSelection = selectedChildrenIds.length > 0;
    const isMutatingSettings = isCreating || isUpdating;
    const isMutatingChildren = addChildToGroupMutation.isPending || removeChildFromGroupMutation.isPending;

    const handleAddSelection = async () => {
        if (!hasAddSelection) return;
        if (isCreate) {
            const selectedNodes = availableSiblings.filter(s => siblingsSelected[s._key]);
            setCurrentChildren(prev => [...prev, ...selectedNodes]);
            setSiblingsSelected({});
        } else {
            await Promise.all(selectedSiblingIds.map(id => addChildToGroupMutation.mutateAsync(id)));
            setSiblingsSelected({});
            // Note: currentChildren will update via query invalidation if the parent re-renders,
            // but to feel "immediate" without a full tree refresh waiting, we could optimistically update.
            // For now, relying on the fact that 'group' prop will change when query invalidates.
        }
    };

    const handleRemoveSelection = async () => {
        if (!hasRemoveSelection) return;
        if (isCreate) {
            setCurrentChildren(prev => prev.filter(c => !childrenSelected[c._key]));
            setChildrenSelected({});
        } else {
            await Promise.all(selectedChildrenIds.map(id => removeChildFromGroupMutation.mutateAsync(id)));
            setChildrenSelected({});
        }
    };

    const onSubmit = (values: GroupFormValues) => {
        if (isCreate) {
            createGroup({
                ...values,
                children_ids: currentChildren.map(c => c._key),
            }, { onSuccess: onClose });
        } else {
            updateGroup(values, { onSuccess: onClose });
        }
    };

    const hasInfoChanges = isCreate ||
        form.watch("name") !== group?.name ||
        form.watch("description") !== (group?.description || "");

    // Update current children if group children changes (for manage mode immediate feel)
    useEffect(() => {
     
        if (!isCreate && group?.children) {
            setCurrentChildren(group.children as ChildCandidate[]);
        }
    }, [group?.children, isCreate]);

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="w-full max-w-3xl sm:max-w-4xl">
                <DialogHeader>
                    <DialogTitle>{title}</DialogTitle>
                </DialogHeader>

                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Name</Label>
                            <Input
                                id="name"
                                {...form.register("name")}
                                placeholder="Enter group name"
                                disabled={isMutatingSettings}
                            />
                            {form.formState.errors.name && (
                                <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
                            )}
                        </div>
                        <div className="space-y-2 col-span-2">
                            <Label htmlFor="description">Description</Label>
                            <Textarea
                                id="description"
                                rows={3}
                                {...form.register("description")}
                                placeholder="Optional description"
                                disabled={isMutatingSettings}
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
                                    <div className="font-medium">Siblings / Available</div>
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
                                type="button"
                                variant="secondary"
                                onClick={handleRemoveSelection}
                                disabled={!hasRemoveSelection || isMutatingChildren}
                            >
                                Remove from children
                            </Button>
                            <Button
                                type="button"
                                onClick={handleAddSelection}
                                disabled={!hasAddSelection || isMutatingChildren}
                            >
                                Add to children
                            </Button>
                        </div>
                        <div className="flex gap-2">
                            <Button type="button" variant="outline" onClick={onClose} disabled={isMutatingSettings}>
                                Cancel
                            </Button>
                            <Button
                                type="submit"
                                disabled={!hasInfoChanges || isMutatingSettings}
                            >
                                {isCreating ? "Creating..." : isUpdating ? "Saving..." : isCreate ? "Create" : "Save"}
                            </Button>
                        </div>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
};

export default GroupDialog;
