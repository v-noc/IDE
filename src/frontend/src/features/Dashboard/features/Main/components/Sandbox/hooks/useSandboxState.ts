import { useRef, useState } from "react";
import { type PlayGroundHandle } from "../features/Playground";

/**
 * Hook to manage Sandbox UI state and interactions.
 */
export function useSandboxState() {
    const [activeTab, setActiveTab] = useState("playground");
    const [isRunning, setIsRunning] = useState(false);
    const playgroundRef = useRef<PlayGroundHandle>(null);

    const handleRun = () => {
        playgroundRef.current?.run();
    };

    const handleOpenSettings = () => {
        playgroundRef.current?.openSettings();
    };

    return {
        activeTab,
        setActiveTab,
        isRunning,
        setIsRunning,
        playgroundRef,
        handleRun,
        handleOpenSettings,
    };
}
