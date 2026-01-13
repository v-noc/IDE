import { useState, useMemo, useCallback } from "react";
import { type SelectableItem } from "../components/SelectableList";
import { useRunCode } from "@/features/Dashboard/features/Main/hooks/usePlayGround";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";

/**
 * Hook to manage Playground internal state.
 */
export function usePlaygroundState(onRunningChange?: (isRunning: boolean) => void) {
    const [code, setCode] = useState("# write your code here");
    const [items, setItems] = useState<SelectableItem[]>([
        { id: "playground", label: "Playground" },
    ]);
    const [selectedId, setSelectedId] = useState<string | undefined>("playground");
    const [output, setOutput] = useState<string>("");
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [examplesPath, setExamplesPath] = useState("");
    const [commandPrefix, setCommandPrefix] = useState("python");

    const project = useProjectStore((s) => s.projectData);
    const runCode = useRunCode(project?._key);

    const handleRun = useCallback(async () => {
        onRunningChange?.(true);
        const relativeFile = selectedId === "playground" ? "playground.py" : `${selectedId}.py`;
        const fullPath = `${examplesPath}/${relativeFile}`;
        const runCommand = `${commandPrefix} ${fullPath}`;
        setOutput(`Command: ${runCommand}`);

        try {
            const resp = await runCode.mutateAsync({
                code,
                executable_path: null,
                examples_path: examplesPath,
                command_prefix: commandPrefix,
                filename: relativeFile,
            });
            setOutput((prev) => `${prev}\n${resp.response}`);
        } catch {
            setOutput((prev) => `${prev}\nError running code`);
        } finally {
            onRunningChange?.(false);
        }
    }, [code, selectedId, examplesPath, commandPrefix, runCode, onRunningChange]);

    const handleAddSnippet = useCallback(() => {
        const newId = `snippet-${Math.random().toString(36).slice(2, 8)}`;
        const newItem = { id: newId, label: `Snippet ${items.length}` };
        setItems((prev) => [...prev, newItem]);
        setSelectedId(newId);
    }, [items.length]);

    const handleRemoveSnippet = useCallback((id: string) => {
        if (id === "playground") return;
        setItems((prev) => prev.filter((x) => x.id !== id));
        if (selectedId === id) setSelectedId("playground");
    }, [selectedId]);

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
        handleRun,
        handleAddSnippet,
        handleRemoveSnippet,
    };
}
