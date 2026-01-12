import { useCallback } from 'react';
import { useRightSidebarActions } from './useRightSidebarActions';
import type { BasicInfoData, CustomizationData } from '../types';
import type { ThemeConfig } from '@/types/project';

/**
 * Event handlers for Right Sidebar interactions.
 * Connects the UI (forms) to the Actions (Store/API).
 */
export function useRightSidebarHandlers() {
    const { updateTheme, updateBasicInfo } = useRightSidebarActions();

    const handleThemeChange = useCallback((data: CustomizationData) => {
        const theme: ThemeConfig = {
            iconColor: data.iconColor,
            cardColor: data.cardColor,
            navbarColor: data.navbarColor,
            leftSidebarColor: data.leftSidebarColor ?? "#f9f9f9",
            rightSidebarColor: data.rightSidebarColor ?? "#f9f9f9",
            backgroundColor: data.backgroundColor ?? "#f9f9f9",
            textColor: data.textColor,
        };
        updateTheme(theme);
    }, [updateTheme]);

    const handleBasicInfoChange = useCallback((data: BasicInfoData) => {
        updateBasicInfo({
            name: data.name,
            description: data.description ?? "",
            icon: data.icon ?? "",
        });
    }, [updateBasicInfo]);

    return {
        handleThemeChange,
        handleBasicInfoChange,
    };
}
