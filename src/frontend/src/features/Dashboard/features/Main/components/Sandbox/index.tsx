import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Play, Settings } from "lucide-react";
import Playground from "./features/Playground";
import LogsContainer from "./features/Logs";
import Test from "./features/Test";
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
    playgroundRef,
    handleRun,
    handleOpenSettings,
  } = useSandboxState();

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

        <div className="border bg-white justify-end flex items-center gap-2 pr-2 w-full h-full">
          {activeTab === "playground" ? (
            <>
              <Button
                size="sm"
                onClick={handleRun}
                disabled={isRunning}
                className="rounded-full bg-green-500 hover:bg-green-600 text-xs h-7 gap-2 px-4 shadow-sm transition-all active:scale-95"
              >
                <Play className="size-3 fill-current" />
                {isRunning ? "Running..." : "Run"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="size-7 rounded-full p-0 flex items-center justify-center hover:bg-accent border shadow-sm transition-all active:scale-95"
                onClick={handleOpenSettings}
              >
                <Settings className="size-3.5 text-muted-foreground" />
              </Button>
            </>
          ) : (
            <div className="text-[10px] font-bold text-muted-foreground/60 px-2 uppercase tracking-widest">
              {activeTab} Mode
            </div>
          )}
        </div>
      </TabsList>

      <div className="flex-1 min-h-0 relative bg-white/30">
        <TabsContent
          value="playground"
          className="m-0 h-full overflow-hidden outline-none"
        >
          <Playground ref={playgroundRef} onRunningChange={setIsRunning} />
        </TabsContent>

        <TabsContent
          value="test"
          className="m-0 h-full overflow-hidden p-6 outline-none"
        >
          <Test />
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
