import Test from "./test";
import PlayGround from "./playGround";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Sandbox() {
  return (
    <div className="p-2">
      <Tabs defaultValue="test" className="flex flex-col">
        <TabsList>
          <TabsTrigger value="test">Test</TabsTrigger>
          <TabsTrigger value="playground">Playground</TabsTrigger>
        </TabsList>
        <TabsContent value="test" className="mt-2">
          <div className="rounded border p-2">
            <Test />
          </div>
        </TabsContent>
        <TabsContent value="playground" className="mt-2">
          <div className="rounded border p-2">
            <PlayGround />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
