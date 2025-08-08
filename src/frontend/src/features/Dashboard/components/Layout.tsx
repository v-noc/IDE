import { ResizableHandle, ResizablePanel } from "@/components/ui/resizable";
import { useState } from "react";
import { ChevronLeft } from "lucide-react";

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

  return (
    <div className="relative flex min-h-screen max-h-screen bg-gray-100 w-full h-full">
      {/* Left Sidebar */}
      {/* <aside className="w-64 max-h-screen overflow-y-auto  p-4 hidden md:block"> */}
      <ResizablePanel defaultSize={20}>{leftSidebar}</ResizablePanel>
      {/* </aside> */}
      <ResizableHandle withHandle />
      {/* Main Content Area */}
      <ResizablePanel
        defaultSize={rightSidebar ? 60 : 80}
        className="flex-1 flex flex-col w-full"
      >
        {/* Navbar */}
        <nav className="p-4 border-b shadow-sidebar">{navbar}</nav>

        {/* Content */}
        <main className="flex-1 min-h-0 h-full">{main}</main>
      </ResizablePanel>

      {/* Right Sidebar (collapsible) */}
      {rightSidebar && isRightOpen && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={20} minSize={12} collapsible>
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
