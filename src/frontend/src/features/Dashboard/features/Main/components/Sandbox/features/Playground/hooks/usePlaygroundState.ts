import { useState, useMemo, useCallback, useEffect, useRef } from "react";
import { type SelectableItem } from "../components/SelectableList";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { AnyNodeTree, CallNodeTree } from "@/types/project";
import type { CreatePlaygroundPayload } from "@/types/playground";
import {
  useCreatePlayground,
  useDeletePlayground,
  usePlaygroundsByOwner,
  useRunPlaygroundCode,
  useUpdatePlayground,
} from "@/services/playground";
import { toast } from "sonner";
import type { PlaygroundFormValues } from "../components/PlaygroundFormDialog";

/**
 * Hook to manage Playground internal state.
 */
const DEFAULT_CODE = "# write your code here";

function toEffectiveNode(
  selectedNode: AnyNodeTree | null | undefined,
  secondarySelectedNode: AnyNodeTree | null | undefined
) {
  if (secondarySelectedNode) {
    if ((secondarySelectedNode as CallNodeTree).target) {
      return (secondarySelectedNode as CallNodeTree).target;
    }
    return secondarySelectedNode;
  }
  if (selectedNode?.node_type === "call") {
    return (selectedNode as CallNodeTree).target;
  }
  return selectedNode;
}

function getOwnerFieldPayload(
  nodeId: string,
  nodeType: string
): Pick<
  CreatePlaygroundPayload,
  "owner_function" | "owner_class" | "owner_file" | "owner_folder"
> {
  if (nodeType === "function") return { owner_function: nodeId };
  if (nodeType === "class") return { owner_class: nodeId };
  if (nodeType === "file") return { owner_file: nodeId };
  if (nodeType === "folder") return { owner_folder: nodeId };
  throw new Error("Playground owner must be function, class, file, or folder");
}

export function usePlaygroundState(
  tabId: string,
  onRunningChange?: (isRunning: boolean) => void
) {
  const [code, setCode] = useState("# write your code here");
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [output, setOutput] = useState<string>("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [examplesPath, setExamplesPath] = useState("");
  const [commandPrefix, setCommandPrefix] = useState("python");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPlaygroundId, setEditingPlaygroundId] = useState<string | null>(
    null
  );
  const [formValues, setFormValues] = useState<PlaygroundFormValues>({
    name: "",
    description: "",
    relative_path: "",
    executable_path: "",
    filename: "playground.py",
  });

  const project = useProjectStore((s) => s.projectData);
  const selectedNode = useProjectStore((s) => s.selectedNode[tabId]);
  const secondarySelectedNode = useProjectStore(
    (s) => s.secondarySelectedNode[tabId]
  );
  const projectId = project?.id ?? "";
  const effectiveNode = useMemo(
    () => toEffectiveNode(selectedNode, secondarySelectedNode),
    [selectedNode, secondarySelectedNode]
  );
  const ownerNodeId = effectiveNode?.id ?? null;

  const { data: playgrounds = [] } = usePlaygroundsByOwner(ownerNodeId, projectId);
  const createPlayground = useCreatePlayground(projectId);
  const updatePlayground = useUpdatePlayground(projectId);
  const deletePlayground = useDeletePlayground(projectId);
  const runPlaygroundCode = useRunPlaygroundCode(projectId);
  const codeUpdateTimer = useRef<number | null>(null);
  const didHydrateCodeRef = useRef(false);

  const items = useMemo<SelectableItem[]>(
    () =>
      playgrounds.map((item) => ({
        id: item.id,
        label: item.name || item.filename || "Untitled playground",
      })),
    [playgrounds]
  );

  const selectedPlayground = useMemo(
    () => playgrounds.find((item) => item.id === selectedId) ?? null,
    [playgrounds, selectedId]
  );

  useEffect(() => {
    if (!playgrounds.length) {
      setSelectedId(undefined);
      setCode(DEFAULT_CODE);
      didHydrateCodeRef.current = false;
      return;
    }

    const currentExists = playgrounds.some((item) => item.id === selectedId);
    if (!selectedId || !currentExists) {
      setSelectedId(playgrounds[0].id);
    }
  }, [playgrounds, selectedId]);

  useEffect(() => {
    if (!selectedPlayground) return;
    setCode(selectedPlayground.code || DEFAULT_CODE);
    didHydrateCodeRef.current = true;
  }, [selectedPlayground?.id]);

  const handleRun = useCallback(async () => {
    if (!selectedPlayground) {
      setOutput("Create or select a playground first.");
      return;
    }
    onRunningChange?.(true);
    setOutput("Running playground...");

    try {
      const resp = await runPlaygroundCode.mutateAsync({
        playground_id: selectedPlayground.id,
      });
      setOutput(resp.response || "");
    } catch {
      setOutput("Error running code");
    } finally {
      onRunningChange?.(false);
    }
  }, [onRunningChange, runPlaygroundCode, selectedPlayground]);

  useEffect(() => {
    if (!selectedPlayground || !didHydrateCodeRef.current) return;
    if (code === (selectedPlayground.code || "")) return;

    if (codeUpdateTimer.current) {
      window.clearTimeout(codeUpdateTimer.current);
    }
    codeUpdateTimer.current = window.setTimeout(() => {
      void updatePlayground.mutateAsync({
        playgroundId: selectedPlayground.id,
        payload: { code },
      });
    }, 500);

    return () => {
      if (codeUpdateTimer.current) {
        window.clearTimeout(codeUpdateTimer.current);
      }
    };
  }, [code, selectedPlayground, updatePlayground]);

  const handleAddSnippet = useCallback(() => {
    if (!effectiveNode?.id || !effectiveNode?.node_type) {
      toast.error("Select a function, class, file, or folder first.");
      return;
    }
    if (
      !["function", "class", "file", "folder"].includes(effectiveNode.node_type)
    ) {
      toast.error("Playground owner must be function, class, file, or folder.");
      return;
    }
    setEditingPlaygroundId(null);
    setFormValues({
      name: "",
      description: "",
      relative_path: "",
      executable_path: "",
      filename: "playground.py",
    });
    setDialogOpen(true);
  }, [effectiveNode]);

  const handleEditSnippet = useCallback(() => {
    if (!selectedPlayground) return;
    setEditingPlaygroundId(selectedPlayground.id);
    setFormValues({
      name: selectedPlayground.name || "",
      description: selectedPlayground.description || "",
      relative_path: selectedPlayground.relative_path || "",
      executable_path: selectedPlayground.executable_path || "",
      filename: selectedPlayground.filename || "",
    });
    setDialogOpen(true);
  }, [selectedPlayground]);

  const handleSubmitDialog = useCallback(async () => {
    const name = formValues.name.trim();
    const relativePath = formValues.relative_path.trim();
    if (!name || !relativePath) {
      toast.error("Name and relative path are required.");
      return;
    }

    if (editingPlaygroundId) {
      await updatePlayground.mutateAsync({
        playgroundId: editingPlaygroundId,
        payload: {
          name,
          description: formValues.description,
          relative_path: relativePath,
          executable_path: formValues.executable_path || null,
          filename: formValues.filename || null,
        },
      });
      setDialogOpen(false);
      return;
    }

    if (!effectiveNode?.id || !effectiveNode?.node_type) {
      toast.error("Select a valid owner node first.");
      return;
    }

    let ownerFieldPayload: ReturnType<typeof getOwnerFieldPayload>;
    try {
      ownerFieldPayload = getOwnerFieldPayload(effectiveNode.id, effectiveNode.node_type);
    } catch (error) {
      toast.error((error as Error).message);
      return;
    }

    const created = await createPlayground.mutateAsync({
      name,
      description: formValues.description,
      relative_path: relativePath,
      executable_path: formValues.executable_path || null,
      filename: formValues.filename || null,
      code: code || DEFAULT_CODE,
      ...ownerFieldPayload,
    });
    setSelectedId(created.id);
    setDialogOpen(false);
  }, [
    code,
    createPlayground,
    editingPlaygroundId,
    effectiveNode,
    formValues,
    updatePlayground,
  ]);

  const handleRemoveSnippet = useCallback((id: string) => {
    void deletePlayground.mutateAsync(id);
    if (selectedId === id) setSelectedId(undefined);
  }, [deletePlayground, selectedId]);

  return {
    code,
    setCode,
    items,
    selectedId,
    setSelectedId,
    output,
    setOutput,
    settingsOpen,
    setSettingsOpen,
    examplesPath,
    setExamplesPath,
    commandPrefix,
    setCommandPrefix,
    dialogOpen,
    setDialogOpen,
    formValues,
    setFormValues,
    editingPlaygroundId,
    isDialogSubmitting: createPlayground.isPending || updatePlayground.isPending,
    handleRun,
    handleAddSnippet,
    handleEditSnippet,
    handleSubmitDialog,
    handleRemoveSnippet,
  };
}
