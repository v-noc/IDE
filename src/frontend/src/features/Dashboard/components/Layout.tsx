import type { ReactNode } from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useResolvedTheme } from "../hooks/useResolvedTheme";
import { usePanelState } from "../hooks/usePanelState";

interface LayoutProps {
  main: ReactNode;
  navbar: ReactNode;
  leftSidebar: ReactNode;
  rightSidebar?: ReactNode;
}
export default function Layout({ navbar, leftSidebar, main }: LayoutProps) {
  // Theme - pure derived state
  const { cssVariables } = useResolvedTheme();

  // Panel state - encapsulated logic
  const leftPanel = usePanelState(true);

  return (
    <div
      className="flex h-screen w-full flex-col overflow-hidden transition-colors duration-300"
      style={cssVariables}
    >
      <ResizablePanelGroup direction="horizontal">
        {/* Left Sidebar Slot */}
        <ResizablePanel
          ref={leftPanel.ref}
          defaultSize={20}
          collapsible
          collapsedSize={0}
          minSize={15}
          maxSize={30}
          onCollapse={leftPanel.onCollapse}
          onExpand={leftPanel.onExpand}
          className="relative border-r bg-(--left-sidebar-color) transition-colors"
        >
          {/* Collapse trigger */}
          <button
            onClick={leftPanel.close}
            aria-label="Collapse sidebar"
            className="absolute right-2 top-2 z-10 rounded-full p-1.5 opacity-0 hover:bg-black/10 group-hover:opacity-100 transition-opacity"
          >
            <ChevronLeft size={16} />
          </button>

          {leftSidebar}
        </ResizablePanel>

        <ResizableHandle className="w-px hover:bg-border/50 transition-colors" />

        {/* Main Content */}
        <ResizablePanel defaultSize={80} className="flex flex-col">
          {/* Navbar Slot */}
          <nav className="border-b bg-(--navbar-color) transition-colors">
            {navbar}
          </nav>

          {/* Main Content Slot */}
          <main className="flex-1 min-h-0 relative overflow-hidden">
            {/* Expand trigger (when collapsed) */}
            {!leftPanel.isOpen && (
              <button
                onClick={leftPanel.open}
                aria-label="Expand sidebar"
                className="absolute left-4 top-4 z-50 rounded-lg bg-white p-2 shadow-md hover:bg-gray-50"
              >
                <ChevronRight size={16} />
              </button>
            )}

            {main}
          </main>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
