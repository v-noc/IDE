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
      <TabsList className="p-0 w-full bg-card flex items-center text-muted-foreground border-b border-border">
        <TabsTrigger
          value="playground"
          className="rounded-none bg-card border-x border-b border-border border-t-2 border-t-transparent text-muted-foreground data-[state=active]:border-t-primary data-[state=active]:text-foreground data-[state=active]:shadow-none data-[state=active]:bg-transparent"
        >
          Playground
        </TabsTrigger>
        <TabsTrigger
          value="test"
          className="rounded-none bg-card border-x border-b border-border border-t-2 border-t-transparent text-muted-foreground data-[state=active]:border-t-primary data-[state=active]:text-foreground data-[state=active]:shadow-none data-[state=active]:bg-transparent"
        >
          Test
        </TabsTrigger>
        <TabsTrigger
          value="logs"
          className="rounded-none bg-card border-x border-b border-border border-t-2 border-t-transparent text-muted-foreground data-[state=active]:border-t-primary data-[state=active]:text-foreground data-[state=active]:shadow-none data-[state=active]:bg-transparent"
        >
          Logs
        </TabsTrigger>

        <div className="border-l border-border bg-card justify-end flex items-center w-full h-full">
          <SandboxToolbar
            variant={toolbarVariant}
            modeLabel={activeTab}
            isRunning={isRunning}
            onRun={handleRun}
            onOpenSettings={handleOpenSettings}
          />
        </div>
      </TabsList>

      <div className="flex-1 min-h-0 relative bg-background/80">
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
