import { ResizableHandle, ResizablePanel } from "@/components/ui/resizable";

const Layout = ({
  main,
  navbar,
  leftSidebar,
}: {
  main: React.ReactNode;
  navbar: React.ReactNode;
  leftSidebar: React.ReactNode;
}) => {
  return (
    <div className="flex min-h-screen bg-gray-100 w-full h-full">
      {/* Left Sidebar */}
      {/* <aside className="w-64 max-h-screen overflow-y-auto  p-4 hidden md:block"> */}
      <ResizablePanel defaultSize={20}>{leftSidebar}</ResizablePanel>
      {/* </aside> */}
      <ResizableHandle withHandle />
      {/* Main Content Area */}
      <ResizablePanel defaultSize={80} className="flex-1 flex flex-col w-full">
        {/* Navbar */}
        <nav className="p-4 border-b shadow-sidebar">{navbar}</nav>

        {/* Content */}
        <main className="flex-1 p-6">{main}</main>
      </ResizablePanel>
    </div>
  );
};

export default Layout;
