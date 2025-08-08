import Layout from "@/features/Dashboard/components/Layout";
import SideBar from "@/features/Dashboard/features/Sidebar/components/SideBar";
import Navbar from "@/features/Dashboard/features/Navbar/componets/Navbar";
import MainCanvas from "@/features/Dashboard/features/Canvas";
import { useParams } from "react-router";

import { ResizablePanelGroup } from "@/components/ui/resizable";
import MainWithRightSidebar from "@/features/Dashboard/features/Canvas/MainWithRightSidebar";
import { RightSidebar } from "@/features/Dashboard/features/Canvas/componets/sidebar";
import ConfigSidebarContent from "@/features/Dashboard/features/Canvas/componets/sidebar/components/SidebarTabs";

const Dashboard = () => {
  const { projectId } = useParams();
  console.log(projectId);
  return (
    <ResizablePanelGroup direction="horizontal">
      <Layout
        main={
          <MainWithRightSidebar
            left={<MainCanvas />}
            right={
              <RightSidebar>
                <ConfigSidebarContent />
              </RightSidebar>
            }
          />
        }
        navbar={<Navbar />}
        leftSidebar={<SideBar />}
      />
    </ResizablePanelGroup>
  );
};

export default Dashboard;
