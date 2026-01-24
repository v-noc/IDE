import React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import BasicInfoSection from "./sections/BasicInfoSection";
import CustomizationSection from "./sections/CustomizationSection";
import {
  useConfigSidebarForm,
  type BasicInfoData,
  type CustomizationData,
} from "../hooks/useConfigSidebarForm";
import DocumentsList from "./sections/DocumentsList";

export type ConfigSidebarContentProps = {
  initialBasicInfo: Partial<BasicInfoData>;
  initialCustomization: Partial<CustomizationData>;
  onChangeBasicInfo?: (data: BasicInfoData) => void;
  onChangeCustomization?: (data: CustomizationData) => void;
  defaultTab?: "documents" | "basic" | "customization";
};

const ConfigSidebarContent: React.FC<ConfigSidebarContentProps> = ({
  initialBasicInfo,
  initialCustomization,
  onChangeBasicInfo,
  onChangeCustomization,
  defaultTab = "documents",
}) => {
  const {
    basicInfo,
    customization,
    handleBasicInfoChange,
    handleCustomizationChange,
  } = useConfigSidebarForm({
    initialBasicInfo,
    initialCustomization,
    onChangeBasicInfo,
    onChangeCustomization,
  });

  return (
    <div className="flex flex-col h-full  ">
      <Tabs defaultValue={defaultTab} className="flex flex-col flex-1 min-h-0">
        <TabsList className="p-0 bg-(--right-sidebar-color)">
          <TabsTrigger
            className="rounded-none bg-white shadow-sm data-[state=active]:border-none data-[state=active]:shadow-none data-[state=active]:bg-transparent"
            value="documents"
          >
            Documents
          </TabsTrigger>
          <TabsTrigger
            className="rounded-none bg-white shadow-sm data-[state=active]:border-none data-[state=active]:shadow-none data-[state=active]:bg-transparent"
            value="basic"
          >
            Basic Info
          </TabsTrigger>

        </TabsList>
        <div className="mt-2 flex-1 min-h-0 overflow-y-auto p-3 py-0 pb-4 ">
          <TabsContent value="basic" className="flex flex-col gap-2 pr-2">
            <BasicInfoSection
              value={basicInfo}
              onChange={handleBasicInfoChange}
            />
            <CustomizationSection
              value={customization}
              onChange={handleCustomizationChange}
            />
          </TabsContent>


          <TabsContent value="documents">
            <DocumentsList />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
};

export default ConfigSidebarContent;
