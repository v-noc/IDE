import { useMemo } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useParams } from "react-router";
import Canvas from "@/features/Dashboard/features/Main/components/canvas";
import useProjectStore from "../../store/useProjectStore";

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
        defaultValue="code"
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
          <TabsContent value="code" className="flex-1">
            <div className="h-full w-full rounded-md border p-4">
              MainCanvas {projectId}
            </div>
          </TabsContent>
        )}

        <TabsContent value="docs" className="flex-1">
          <div className="h-full w-full rounded-md border p-4">
            Documentation for project {projectId}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MainCanvas;
