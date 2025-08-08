import { useEffect, useState, useRef, useCallback } from "react";
import * as z from "zod";

export const basicInfoSchema = z.object({
    name: z.string().min(1, "Name is required").max(200, "Name is too long"),
    description: z.string().max(5000, "Description is too long"),
    icon: z.string().optional(),
});
export type BasicInfoData = z.infer<typeof basicInfoSchema>;

export const customizationSchema = z.object({
    iconColor: z.string(),
    nameColor: z.string(),
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
    nameColor: "#000000",
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

    const basicTimeoutRef = useRef<number>();
    const customTimeoutRef = useRef<number>();

    useEffect(() => {
        setBasicInfo({ ...defaultBasic, ...initialBasicInfo });
    }, [JSON.stringify(initialBasicInfo)]);

    useEffect(() => {
        setCustomization({ ...defaultCustom, ...initialCustomization });
    }, [JSON.stringify(initialCustomization)]);

    const handleBasicInfoChange = useCallback(
        (data: BasicInfoData) => {
            setBasicInfo(data);
            clearTimeout(basicTimeoutRef.current);
            basicTimeoutRef.current = window.setTimeout(() => {
                onChangeBasicInfo?.(data);
            }, DEBOUNCE_MS);
        },
        [onChangeBasicInfo]
    );

    const handleCustomizationChange = useCallback(
        (data: CustomizationData) => {
            setCustomization(data);
            clearTimeout(customTimeoutRef.current);
            customTimeoutRef.current = window.setTimeout(() => {
                onChangeCustomization?.(data);
            }, DEBOUNCE_MS);
        },
        [onChangeCustomization]
    );

    useEffect(() => {
        return () => {
            clearTimeout(basicTimeoutRef.current);
            clearTimeout(customTimeoutRef.current);
        };
    }, []);

    return {
        basicInfo,
        customization,
        handleBasicInfoChange,
        handleCustomizationChange,
    };
}; 