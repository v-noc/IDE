import { useRef, useState } from "react";
import { type PlayGroundHandle } from "../features/Playground";
import type { TestHandle } from "../features/Test";

/**
 * Hook to manage Sandbox UI state and interactions.
 */
export function useSandboxState() {
  const [activeTab, setActiveTab] = useState("playground");
  const [isRunning, setIsRunning] = useState(false);
  const [isTestConfigCreated, setIsTestConfigCreated] = useState(false);
  const playgroundRef = useRef<PlayGroundHandle>(null);
  const testRef = useRef<TestHandle>(null);

  const handleRun = () => {
    if (activeTab === "playground") {
      playgroundRef.current?.run();
      return;
    }
    if (activeTab === "test") {
      testRef.current?.run();
    }
  };

  const handleOpenSettings = () => {
    if (activeTab === "playground") {
      playgroundRef.current?.openSettings();
      return;
    }
    if (activeTab === "test") {
      testRef.current?.openSettings();
    }
  };

  return {
    activeTab,
    setActiveTab,
    isRunning,
    setIsRunning,
    isTestConfigCreated,
    setIsTestConfigCreated,
    playgroundRef,
    testRef,
    handleRun,
    handleOpenSettings,
  };
}
