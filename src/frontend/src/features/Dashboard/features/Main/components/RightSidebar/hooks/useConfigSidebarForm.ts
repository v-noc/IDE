import { useEffect, useState, useMemo, useCallback } from "react";
import * as z from "zod";
import { debounce } from "remeda";

export const basicInfoSchema = z.object({
  name: z.string().min(1, "Name is required").max(200, "Name is too long"),
  description: z.string().max(5000, "Description is too long"),
  icon: z.string().optional(),
});
export type BasicInfoData = z.infer<typeof basicInfoSchema>;

export const customizationSchema = z.object({
  iconColor: z.string(),
  cardColor: z.string(),
  navbarColor: z.string().optional(),
  leftSidebarColor: z.string().optional(),
  rightSidebarColor: z.string().optional(),
  backgroundColor: z.string().optional(),
  textColor: z.string().optional(),
  fontSize: z.number().optional(),
});
export type CustomizationData = z.infer<typeof customizationSchema>;

const defaultBasic: BasicInfoData = {
  name: "",
  description: "",
  icon: undefined,
};
const defaultCustom: Omit<CustomizationData, "navbarColor" | "leftSidebarColor" | "rightSidebarColor" | "backgroundColor" | "textColor" | "fontSize"> = {
  iconColor: "#000000",

  cardColor: "#ffffff",
};

const DEBOUNCE_MS = 500;

export const useConfigSidebarForm = ({
  initialBasicInfo,
  initialCustomization,
  onChangeBasicInfo,
  onChangeCustomization,
}: {
  initialBasicInfo: Partial<BasicInfoData>;
  initialCustomization: Partial<CustomizationData>;
  onChangeBasicInfo?: (data: BasicInfoData) => void;
  onChangeCustomization?: (data: CustomizationData) => void;
}) => {
  const [basicInfo, setBasicInfo] = useState<BasicInfoData>({
    ...defaultBasic,
    ...initialBasicInfo,
  });
  const [customization, setCustomization] = useState<CustomizationData>({
    ...defaultCustom,
    ...initialCustomization,
  });

  useEffect(() => {
    setBasicInfo({ ...defaultBasic, ...initialBasicInfo });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(initialBasicInfo)]);

  useEffect(() => {
    setCustomization({ ...defaultCustom, ...initialCustomization });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(initialCustomization)]);

  const debouncedBasicInfoChange = useMemo(
    () =>
      debounce(
        (data: BasicInfoData) => {
          onChangeBasicInfo?.(data);
        },
        { waitMs: DEBOUNCE_MS }
      ),
    [onChangeBasicInfo]
  );

  const debouncedCustomizationChange = useMemo(
    () =>
      debounce(
        (data: CustomizationData) => {
          onChangeCustomization?.(data);
        },
        { waitMs: DEBOUNCE_MS }
      ),
    [onChangeCustomization]
  );

  const handleBasicInfoChange = useCallback(
    (data: BasicInfoData) => {
      setBasicInfo(data);
      debouncedBasicInfoChange.call(data);
    },
    [debouncedBasicInfoChange]
  );

  const handleCustomizationChange = useCallback(
    (data: CustomizationData) => {
      setCustomization(data);
      debouncedCustomizationChange.call(data);
    },
    [debouncedCustomizationChange]
  );

  return {
    basicInfo,
    customization,
    handleBasicInfoChange,
    handleCustomizationChange,
  };
}; 
