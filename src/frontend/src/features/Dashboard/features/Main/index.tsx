import { useMemo } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useParams } from "react-router";
import Canvas from "@/features/Dashboard/features/Main/components/canvas";
import useProjectStore from "../../store/useProjectStore";
import Documents from "./components/docs";
import EditorCode from "./components/code";

const MainCanvas = () => {
  const { projectId } = useParams();
  const { selectedNode } = useProjectStore();

  const isCanvasActive = useMemo(() => {
    return selectedNode?.type === "function" || selectedNode?.type === "class";
  }, [selectedNode?.type]);

  const isCodeActive = useMemo(() => {
    return (
      selectedNode?.type === "function" ||
      selectedNode?.type === "class" ||
      selectedNode?.type == "file"
    );
  }, [selectedNode?.type]);

  return (
    <div className="flex h-full w-full flex-col gap-2 p-2">
      <Tabs
        defaultValue={isCodeActive ? "code" : "docs"}
        className="flex h-full w-full flex-col bg-background rounded"
      >
        <TabsList>
          {isCodeActive && <TabsTrigger value="code">Code</TabsTrigger>}
          {isCanvasActive && <TabsTrigger value="canvas">Canvas</TabsTrigger>}
          <TabsTrigger value="docs">Docs</TabsTrigger>
        </TabsList>
        {isCanvasActive && (
          <TabsContent value="canvas" className="flex-1">
            <div className="h-full w-full rounded-md border">
              <Canvas projectId={projectId} />
            </div>
          </TabsContent>
        )}
        {isCodeActive && (
          <TabsContent
            value="code"
            className="flex-1 flex flex-col overflow-hidden"
          >
            <div className="h-full w-full overflow-auto py-4">
              <EditorCode />
            </div>
          </TabsContent>
        )}

        <TabsContent
          value="docs"
          className="flex-1 flex flex-col overflow-hidden"
        >
          <div className="flex-1 rounded-md border overflow-hidden">
            <div className="h-full w-full overflow-auto py-4">
              <Documents />
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MainCanvas;
