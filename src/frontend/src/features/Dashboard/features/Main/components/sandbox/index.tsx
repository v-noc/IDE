import { useRef, useState } from "react";
import Test from "./components/Test";
import PlayGround, { type PlayGroundHandle } from "./components/PlayGround";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Play, Settings } from "lucide-react";

export default function Sandbox() {
  const [activeTab, setActiveTab] = useState("playground");
  const [isRunning, setIsRunning] = useState(false);
  const playgroundRef = useRef<PlayGroundHandle>(null);

  return (
    <Tabs
      value={activeTab}
      onValueChange={setActiveTab}
      className="flex flex-col h-full "
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
        <div className="border bg-white justify-end flex items-center gap-2 pr-2 w-full h-full">
          {activeTab === "playground" ? (
            <>
              <Button
                size="sm"
                onClick={() => playgroundRef.current?.run()}
                disabled={isRunning}
                className="rounded-full bg-green-500 text-xs h-6"
              >
                <Play className=" h-1 w-1" />
                {isRunning ? "Running..." : "Run"}
              </Button>
              <Button
                className="w-6 h-6 rounded-full flex items-center justify-center"
                variant="outline"
                onClick={() => playgroundRef.current?.openSettings()}
              >
                <Settings className=" h-4 w-4" />
              </Button>
            </>
          ) : (
            <div className="text-xs text-muted-foreground">Test actions</div>
          )}
        </div>
      </TabsList>
      <TabsContent
        value="test"
        className="mt-2 h-full w-full overflow-hidden p-2"
      >
        <Test />
      </TabsContent>
      <TabsContent value="playground" className="mt-2 overflow-hidden">
        <PlayGround
          ref={playgroundRef}
          onRunningChange={(r) => setIsRunning(r)}
        />
      </TabsContent>
    </Tabs>
  );
}
