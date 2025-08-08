import React, { useMemo, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import BasicInfoSection from "../sections/BasicInfoSection";
import type { BasicInfoData } from "../sections/BasicInfoSection";
import CustomizationSection from "../sections/CustomizationSection";
import type { CustomizationData } from "../sections/CustomizationSection";

export type ConfigSidebarContentProps = {
  initialBasicInfo?: Partial<BasicInfoData>;
  initialCustomization?: Partial<CustomizationData>;
  onChangeBasicInfo?: (data: BasicInfoData) => void;
  onChangeCustomization?: (data: CustomizationData) => void;
  defaultTab?: "basic" | "customization";
};

const defaultBasic: BasicInfoData = {
  name: "",
  description: "",
  icon: undefined,
};
const defaultCustom: CustomizationData = {
  iconColor: "#000000",
  nameColor: "#000000",
  cardColor: "#ffffff",
};

const ConfigSidebarContent: React.FC<ConfigSidebarContentProps> = ({
  initialBasicInfo,
  initialCustomization,
  onChangeBasicInfo,
  onChangeCustomization,
  defaultTab = "basic",
}) => {
  const [basicInfo, setBasicInfo] = useState<BasicInfoData>({
    ...defaultBasic,
    ...initialBasicInfo,
  });
  const [custom, setCustom] = useState<CustomizationData>({
    ...defaultCustom,
    ...initialCustomization,
  });

  const handleBasicChange = (data: BasicInfoData) => {
    setBasicInfo(data);
    onChangeBasicInfo?.(data);
  };

  const handleCustomChange = (data: CustomizationData) => {
    setCustom(data);
    onChangeCustomization?.(data);
  };

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
          </TabsList>
          <div className="mt-2 flex-1 min-h-0 overflow-y-auto pr-1 pb-4">
            <TabsContent value="basic">
              <BasicInfoSection
                value={basicInfo}
                onChange={handleBasicChange}
              />
            </TabsContent>
            <TabsContent value="customization">
              <CustomizationSection
                value={custom}
                onChange={handleCustomChange}
              />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    ),
    [basicInfo, custom, defaultTab]
  );

  return tabs;
};

export default ConfigSidebarContent;
