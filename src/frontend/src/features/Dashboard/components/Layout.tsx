import { ResizableHandle, ResizablePanel } from "@/components/ui/resizable";
import { useEffect, useState } from "react";
import { ChevronLeft } from "lucide-react";
import { useThemeStore } from "../store/useThemeStore";

import useProjectStore from "../store/useProjectStore";

const Layout = ({
  main,
  navbar,
  leftSidebar,
  rightSidebar,
}: {
  main: React.ReactNode;
  navbar: React.ReactNode;
  leftSidebar: React.ReactNode;
  rightSidebar?: React.ReactNode;
}) => {
  const [isRightOpen, setIsRightOpen] = useState(true);
  const { theme, setTheme } = useThemeStore();
  const { projectData } = useProjectStore();

  useEffect(() => {
    if (projectData?.theme) {
      setTheme(projectData.theme);
    }
  }, [projectData, setTheme]);

  const style = theme
    ? ({
        "--navbar-color": theme.navbarColor,
        "--left-sidebar-color": theme.leftSidebarColor,
        "--right-sidebar-color": theme.rightSidebarColor,
        "--background-color": theme.backgroundColor,
        "--text-color": theme.textColor,
        "--icon-color": theme.iconColor,
        "--card-color": theme.cardColor,
      } as React.CSSProperties)
    : {};

  return (
    <div
      className="relative flex min-h-screen max-h-screen w-full h-full"
      style={style}
    >
      {/* Left Sidebar */}
      <ResizablePanel
        defaultSize={20}
        className="bg-[var(--left-sidebar-color)]"
      >
        {leftSidebar}
      </ResizablePanel>
      <ResizableHandle withHandle />
      {/* Main Content Area */}
      <ResizablePanel
        defaultSize={rightSidebar ? 60 : 80}
        className="flex-1 flex flex-col w-full bg-[var(--background-color)]"
      >
        {/* Navbar */}
        <nav className="p-4 border-b shadow-sidebar bg-[var(--navbar-color)]">
          {navbar}
        </nav>

        {/* Content */}
        <main className="flex-1 min-h-0 h-full">{main}</main>
      </ResizablePanel>

      {/* Right Sidebar (collapsible) */}
      {rightSidebar && isRightOpen && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel
            defaultSize={20}
            minSize={12}
            collapsible
            className="bg-[var(--right-sidebar-color)]"
          >
            {rightSidebar}
          </ResizablePanel>
        </>
      )}

      {/* Re-open toggle button when right sidebar is hidden */}
      {rightSidebar && !isRightOpen && (
        <button
          type="button"
          aria-label="Open right sidebar"
          onClick={() => setIsRightOpen(true)}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-50 p-2 bg-white border rounded-l-md shadow hover:bg-gray-50"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
      )}

      {/* Provide a way for the sidebar content to close itself via context (simple prop function) */}
      {/* Consumers can pass a button that calls the provided onClose if desired */}
    </div>
  );
};

export default Layout;
