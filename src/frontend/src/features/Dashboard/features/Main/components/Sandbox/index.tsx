import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Playground from "./features/Playground";
import LogsContainer from "./features/Logs";
import Test from "./features/Test";
import { SandboxToolbar } from "./components/SandboxToolbar";
import { useSandboxState } from "./hooks/useSandboxState";

/**
 * Sandbox Component.
 * Orchestrates multiple features (Playground, Test, Logs) in a tabbed interface.
 */
export default function Sandbox({ tabId }: { tabId: string }) {
  const {
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
  } = useSandboxState();

  const toolbarVariant: "playground" | "test" | "mode-only" =
    activeTab === "playground"
      ? "playground"
      : activeTab === "test" && isTestConfigCreated
        ? "test"
        : "mode-only";

  return (
    <Tabs
      value={activeTab}
      onValueChange={setActiveTab}
      className="flex flex-col h-full"
    >
      <TabsList className="p-0 w-full bg-[#f9f9f9] flex items-center">
        <TabsTrigger
          value="playground"
          className="rounded-none shadow-sm  data-[state=active]:border-none data-[state=active]:shadow-none data-[state=active]:bg-transparent bg-white"
        >
          Playground
        </TabsTrigger>
        <TabsTrigger
          value="test"
          className="rounded-none data-[state=active]:border-none shadow-sm data-[state=active]:shadow-none data-[state=active]:bg-transparent bg-white"
        >
          Test
        </TabsTrigger>
        <TabsTrigger
          value="logs"
          className="rounded-none data-[state=active]:border-none shadow-sm data-[state=active]:shadow-none data-[state=active]:bg-transparent bg-white"
        >
          Logs
        </TabsTrigger>

        <div className="border bg-white justify-end flex items-center w-full h-full">
          <SandboxToolbar
            variant={toolbarVariant}
            modeLabel={activeTab}
            isRunning={isRunning}
            onRun={handleRun}
            onOpenSettings={handleOpenSettings}
          />
        </div>
      </TabsList>

      <div className="flex-1 min-h-0 relative bg-white/30">
        <TabsContent
          value="playground"
          className="m-0 h-full overflow-hidden outline-none"
        >
          <Playground
            ref={playgroundRef}
            tabId={tabId}
            onRunningChange={setIsRunning}
          />
        </TabsContent>

        <TabsContent
          value="test"
          className="m-0 h-full overflow-hidden outline-none"
        >
          <Test
            ref={testRef}
            tabId={tabId}
            onRunningChange={setIsRunning}
            onConfigChange={setIsTestConfigCreated}
          />
        </TabsContent>

        <TabsContent
          value="logs"
          className="m-0 h-full overflow-hidden outline-none"
        >
          <div className="h-full p-2 overflow-y-auto">
            <LogsContainer tabId={tabId} />
          </div>
        </TabsContent>
      </div>
    </Tabs>
  );
}
