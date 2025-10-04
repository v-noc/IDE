import Test from "./test";
import PlayGround from "./playGround";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function Sandbox() {
  return (
    <Tabs defaultValue="playground" className="flex flex-col h-full p-2">
      <TabsList>
        <TabsTrigger value="playground">Playground</TabsTrigger>
        <TabsTrigger value="test">Test</TabsTrigger>
      </TabsList>
      <TabsContent value="test" className="mt-2 h-full w-full ">
        <div className="rounded border p-2">
          <Test />
        </div>
      </TabsContent>
      <TabsContent value="playground" className="mt-2">
        <PlayGround />
      </TabsContent>
    </Tabs>
  );
}
