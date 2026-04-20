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
                <TabsList className="w-full p-0 bg-(--right-sidebar-color) text-muted-foreground">
                    <TabsTrigger
                        className="rounded-none bg-(--right-sidebar-color) border-x border-b border-border border-t-2 border-t-transparent text-muted-foreground data-[state=active]:border-t-primary data-[state=active]:text-foreground data-[state=active]:shadow-none data-[state=active]:bg-transparent"
                        value="calls"
                    >
                        Calls
                    </TabsTrigger>
                    <TabsTrigger
                        className="rounded-none bg-(--right-sidebar-color) border-x border-b border-border border-t-2 border-t-transparent text-muted-foreground data-[state=active]:border-t-primary data-[state=active]:text-foreground data-[state=active]:shadow-none data-[state=active]:bg-transparent"
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
