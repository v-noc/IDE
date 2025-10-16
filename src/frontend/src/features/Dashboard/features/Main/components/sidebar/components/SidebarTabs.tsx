import React, { useMemo } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import BasicInfoSection from "./sections/BasicInfoSection";
import CustomizationSection from "./sections/CustomizationSection";
import {
  useConfigSidebarForm,
  type BasicInfoData,
  type CustomizationData,
} from "../hooks/useConfigSidebarForm";
import LogsSection from "./sections/LogsSection";

export type ConfigSidebarContentProps = {
  initialBasicInfo: Partial<BasicInfoData>;
  initialCustomization: Partial<CustomizationData>;
  onChangeBasicInfo?: (data: BasicInfoData) => void;
  onChangeCustomization?: (data: CustomizationData) => void;
  defaultTab?: "basic" | "customization";
};

const ConfigSidebarContent: React.FC<ConfigSidebarContentProps> = ({
  initialBasicInfo,
  initialCustomization,
  onChangeBasicInfo,
  onChangeCustomization,
  defaultTab = "basic",
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

  const tabs = useMemo(
    () => (
      <div className="flex flex-col h-full p-3">
        <Tabs
          defaultValue={defaultTab}
          className="flex flex-col flex-1 min-h-0"
        >
          <TabsList>
            <TabsTrigger value="basic">Basic Info</TabsTrigger>
            <TabsTrigger value="customization">Customization</TabsTrigger>
            <TabsTrigger value="logs">Logs</TabsTrigger>
          </TabsList>
          <div className="mt-2 flex-1 min-h-0 overflow-y-auto pr-1 pb-4">
            <TabsContent value="basic">
              <BasicInfoSection
                value={basicInfo}
                onChange={handleBasicInfoChange}
              />
            </TabsContent>
            <TabsContent value="customization">
              <CustomizationSection
                value={customization}
                onChange={handleCustomizationChange}
              />
            </TabsContent>
            <TabsContent value="logs">
              <LogsSection />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    ),
    [basicInfo, customization, defaultTab]
  );

  return tabs;
};

export default ConfigSidebarContent;
