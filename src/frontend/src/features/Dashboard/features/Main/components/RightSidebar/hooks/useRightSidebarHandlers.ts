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
            leftSidebarColor: data.leftSidebarColor ?? "#1e1e1e",
            rightSidebarColor: data.rightSidebarColor ?? "#1e1e1e",
            backgroundColor: data.backgroundColor ?? "#121212",
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
