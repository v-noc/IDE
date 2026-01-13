import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import CallSidebar from '../CallSidebar';
import BaseClass from '../BaseClass';

interface RightSidebarTabsProps {
    className?: string;
}

/**
 * Presentational component for the Right Sidebar's bottom tabs.
 * Manages the "Calls" and "Base Class" views.
 */
export function RightSidebarTabs({ className }: RightSidebarTabsProps) {
    return (
        <div className={`h-full min-h-0 flex flex-col ${className ?? ""}`}>
            <Tabs defaultValue="calls" className="flex-1 min-h-0 flex flex-col">
                <TabsList className="w-full p-0 bg-(--right-sidebar-color)">
                    <TabsTrigger
                        className="rounded-none data-[state=active]:border-none shadow-sm data-[state=active]:shadow-none data-[state=active]:bg-transparent bg-white"
                        value="calls"
                    >
                        Calls
                    </TabsTrigger>
                    <TabsTrigger
                        className="rounded-none data-[state=active]:border-none shadow-sm data-[state=active]:shadow-none data-[state=active]:bg-transparent bg-white"
                        value="base"
                    >
                        Base Class
                    </TabsTrigger>
                </TabsList>
                <TabsContent value="calls" className="flex-1 min-h-0">
                    <CallSidebar hideHeader />
                </TabsContent>
                <TabsContent
                    value="base"
                    className="flex-1 min-h-0 overflow-auto px-3 py-2"
                >
                    <BaseClass />
                </TabsContent>
            </Tabs>
        </div>
    );
}
